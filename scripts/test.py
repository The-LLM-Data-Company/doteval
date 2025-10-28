import asyncio
import json
from datetime import datetime
from rubric import Rubric
from rubric.autograders import PerCriterionOneShotGrader, PerCriterionGrader
from rubric.utils import default_generate_fn
from dotenv import load_dotenv
import os
from openai import AsyncOpenAI

load_dotenv()
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

GOLDEN_ANSWER = """
This patient's course is best explained by an unresolved pregnancy-associated thrombotic microangiopathy (TMA), most consistent with postpartum TTP rather than simple persistence of HELLP syndrome. Classically, HELLP improves rapidly once the placenta is delivered, with normalization of liver enzymes and platelet counts within a few days. Persistence of platelets in the 90s and elevated AST/ALT weeks after delivery is atypical for HELLP and suggests another TMA. The recurrent seizures and ongoing visual changes, despite normotension and magnesium sulfate therapy, further support a microvascular process, as magnesium stabilizes endothelium but cannot reverse active microthrombi. 
TTP pathophysiology centers on ADAMTS13 deficiency, leading to accumulation of large von Willebrand factor multimers and uncontrolled platelet aggregation in the microcirculation, producing hepatic injury, cytopenias, and neurologic dysfunction. In contrast, seizures in eclampsia or HELLP are usually due to posterior reversible encephalopathy syndrome (PRES) from vasogenic edema, which typically improves postpartum. The continued seizures here reflect ischemic insults from microthrombotic occlusion rather than endothelial hyperreactivity alone. Key features include the time course (persistence >1-2 weeks postpartum), normotension, and neurologic progression, which make unresolved HELLP unlikely and point toward TTP. 
Next steps should include a peripheral smear for schistocytes, LDH, haptoglobin, indirect bilirubin, and ADAMTS13 activity testing. MRI can help distinguish PRES from ischemic lesions caused by microthrombi. If ADAMTS13 activity is <10 percent or clinical suspicion is high, plasma exchange should be initiated emergently as per American Society of Hematology guidelines, because delay carries high mortality. Adjunctive immunosuppression with corticosteroids is standard, and rituximab can be added if refractory. Magnesium may still be given for endothelial stabilization but is not curative, and seizure protection should be supplemented with an anticonvulsant such as levetiracetam. This case highlights a critical pitfall: attributing seizures weeks postpartum to residual eclampsia or new epilepsy risks missing a life-threatening TMA.
"""

MID_ANSWER = """
This is a brilliant clinical puzzle that highlights a critical diagnostic pitfall. You're describing **atypical hemolytic uremic syndrome (aHUS)** or **thrombotic microangiopathy (TMA)**, likely triggered by pregnancy but never resolving postpartum.

## Why This Isn't Just Eclampsia/Epilepsy:

**The red flags you've identified:**
- Persistent thrombocytopenia (low 90s) 6 weeks postpartum
- Never-normalizing transaminases
- Recurrent seizures despite "normal" blood pressures
- Visual disturbances (microangiopathic changes)
- Magnesium repeatedly failing

## The Real Pathophysiology:

**Complement-mediated TMA** (aHUS):
- Pregnancy is a known trigger for complement dysregulation
- Causes endothelial injury → microangiopathic hemolytic anemia
- Platelet consumption and microvascular thrombosis
- **Affects multiple organs**: liver (transaminitis), kidneys, brain (seizures), eyes (retinal changes)

**Why magnesium keeps failing:**
- Magnesium treats eclamptic seizures by stabilizing neuronal membranes
- It does NOTHING for the underlying endothelial injury and microthrombosis
- The seizures aren't from vasospasm—they're from microvascular ischemia and thrombosis

## Critical Missing Workup:

1. **Peripheral smear** - schistocytes (microangiopathic hemolysis)
2. **LDH** - elevated from hemolysis
3. **Haptoglobin** - low
4. **Creatinine** - may show renal TMA
5. **ADAMTS13 activity** - to distinguish from TTP
6. **Complement studies** - C3, C4, CH50, factor H, factor I

## The Prenatal Vitamin Connection:

This is the most insidious part—**folate deficiency exacerbates TMA**:
- Folate is essential for endothelial repair
- Deficiency worsens homocysteine levels → more endothelial damage
- Stopping prenatals removed a protective factor

## What She Actually Needs:

1. **Eculizumab** (Soliris) or **ravulizumab** - complement C5 inhibitor
   - This is the definitive treatment for aHUS
   - Can be life-saving and prevent progression to ESRD

2. **Plasma exchange** - if TTP can't be excluded or as bridge therapy

3. **Resume folate** supplementation

4. **Nephrology consultation** urgently

## Why This Gets Missed:

- "Severe features" preeclampsia and HELLP overlap with TMA
- Postpartum preeclampsia/eclampsia can occur up to 6 weeks, creating diagnostic anchoring
- Once labeled "epilepsy," the systemic disease gets ignored
- Normal blood pressures falsely reassure

**The key insight**: When "eclampsia" doesn't behave like eclampsia (persistent lab abnormalities, recurrent seizures despite treatment, multiorgan involvement beyond 6 weeks), think **TMA**. This patient needs complement blockade, not just anticonvulsants.
"""

rubric_raw = {"datasetId":"800acfc8-eaf2-4f24-9a8c-ee931540809c","query":"Individual at 26 weeks presents with eclamptic seizure, gets magnesium, improves, delivered at 28 weeks for \"severe features.\" Three weeks postpartum, readmitted with seizure despite normal pressures. Gets keppra, discharged. Shows up again at 6 weeks postpartum with breakthrough seizure - but now nobody's checking liver enzymes or uric acid anymore, and everyone's assuming it's epilepsy from the eclampsia. Looking back, her AST/ALT never normalized, platelets stayed low 90s, and she mentions her vision \"still looks weird sometimes.\" Husband mentions she stopped her prenatal vitamins weeks ago. What's the real underlying disorder driving the persistent hepatic dysfunction and seizure threshold, and why does magnesium alone keep failing?","rubric":{"id":"postpartum-hellp-tma-evaluation","sections":[{"id":"diagnostic-distinctions","title":"Diagnostic Distinctions","criteria":[{"id":"postpartum-ttp","requirement":"States that condition is best explained by postpartum thrombotic thrombocytopenic purpura (TTP)","weight":7},{"id":"hellp-resolution","requirement":"States that HELLP syndrome typically resolves rapidly after delivery with normalization of labs within days ","weight":6},{"id":"atypical-persistence","requirement":"States that persistence of thrombocytopenia and elevated AST/ALT weeks postpartum is atypical for HELLP","weight":5},{"id":"neurological-clues","requirement":"States that continued seizures and visual changes despite normotension and magnesium favor TTP","weight":5}]},{"id":"pathophysiology","title":"Pathophysiology","criteria":[{"id":"adamts13-deficiency","requirement":"States that TTP results from ADAMSTS13 deficiency ","weight":7},{"id":"vwf-multimers","requirement":"States that ADAMTS13 deficiency leads to accumulation of large von Willebrand factor multimers","weight":6},{"id":"platelet-aggregation","requirement":"States that uncontrolled platelet aggregation in microcirculation occurs in TTP","weight":5},{"id":"organ-dysfunction","requirement":"States that microthrombi cause hepatic injury, cytopenias, and neurological dysfunction ","weight":5}]},{"id":"clinical-features","title":"Clinical Features","criteria":[{"id":"time-course","requirement":"States that persistence of symptoms >1-2 weeks postpartum suggests TTP rather than HELLP","weight":5},{"id":"normotension","requirement":"States that normotension despite seizures argues against eclampsia","weight":4},{"id":"seizure-mechanism","requirement":"States that seizures in TTP reflect ischemic insults from microthrombi","weight":4},{"id":"contrast-with-pres","requirement":"States that seizrues in HELLP/eclampsia are usually due to PRES from vasogenic edema","weight":3}]},{"id":"recommended-workup","title":"Recommended Workup","criteria":[{"id":"peripheral-smear","requirement":"Specifies obtaining a peripheral smear for schistocytes","weight":6},{"id":"hemolysis-labs","requirement":"Specifies measuring LDH, haptoglobin, and indirect bilirubin for hemolysis","weight":5},{"id":"adamts13-testing","requirement":"Specifies testing ADAMTS13 activity","weight":5},{"id":"mri-utility","requirement":"Stat that MRI can help distinguish PRES from ischemic lesions","weight":2}]},{"id":"management","title":"Management","criteria":[{"id":"plasma-exchange","requirement":"Recommends emergent plasma exchange if ADAMTS13 activity <10% or clinical suspicion is high","weight":7},{"id":"corticosteroids","requirement":"Recommends corticosteroids as adjunctive immunosuppression","weight":4},{"id":"rituximab","requirement":"Recommends rituximab for refractory disease","weight":3},{"id":"seizure-protection","requirement":"Recommends seizure protection with levetiracetam in addition to magnesium","weight":2}]},{"id":"unsafe-errors","title":"Unsafe Errors","criteria":[{"id":"misdiagnoses-hellp","requirement":"States that persistent symptoms weeks postpartum are due to HELLP syndrome","weight":-25},{"id":"misdiagnoses-eclampsia","requirement":"States that seizures weeks postpartum are due to eclampsia","weight":-20},{"id":"misdiagnoses-epilepsy","requirement":"States that seizures are due to new-onset epilepsy","weight":-15},{"id":"continues-magnesium-only","requirement":"States that magnesium alone is sufficient to treat seizures from TTP","weight":-10}]}]},"goldenResponse":"This patient's course is best explained by an unresolved pregnancy-associated thrombotic microangiopathy (TMA), most consistent with postpartum TTP rather than simple persistence of HELLP syndrome. Classically, HELLP improves rapidly once the placenta is delivered, with normalization of liver enzymes and platelet counts within a few days. Persistence of platelets in the 90s and elevated AST/ALT weeks after delivery is atypical for HELLP and suggests another TMA. The recurrent seizures and ongoing visual changes, despite normotension and magnesium sulfate therapy, further support a microvascular process, as magnesium stabilizes endothelium but cannot reverse active microthrombi. \nTTP pathophysiology centers on ADAMTS13 deficiency, leading to accumulation of large von Willebrand factor multimers and uncontrolled platelet aggregation in the microcirculation, producing hepatic injury, cytopenias, and neurologic dysfunction. In contrast, seizures in eclampsia or HELLP are usually due to posterior reversible encephalopathy syndrome (PRES) from vasogenic edema, which typically improves postpartum. The continued seizures here reflect ischemic insults from microthrombotic occlusion rather than endothelial hyperreactivity alone. Key features include the time course (persistence >1-2 weeks postpartum), normotension, and neurologic progression, which make unresolved HELLP unlikely and point toward TTP. \nNext steps should include a peripheral smear for schistocytes, LDH, haptoglobin, indirect bilirubin, and ADAMTS13 activity testing. MRI can help distinguish PRES from ischemic lesions caused by microthrombi. If ADAMTS13 activity is <10 percent or clinical suspicion is high, plasma exchange should be initiated emergently as per American Society of Hematology guidelines, because delay carries high mortality. Adjunctive immunosuppression with corticosteroids is standard, and rituximab can be added if refractory. Magnesium may still be given for endothelial stabilization but is not curative, and seizure protection should be supplemented with an anticonvulsant such as levetiracetam. This case highlights a critical pitfall: attributing seizures weeks postpartum to residual eclampsia or new epilepsy risks missing a life-threatening TMA."}

# Extract all criteria from the nested sections structure
# The from_json method expects a flat list of criteria, so we need to flatten the nested structure
async def run_single_test(rubric, autograder, answer):
    """Run a single grading test and return the full result"""
    result = await rubric.grade(
        to_grade=answer,
        autograder=autograder
    )
    return result

async def analyze_results_with_gpt(results_summary):
    """Use GPT to analyze the grading results and explain drift"""
    prompt = f"""You are analyzing results from an autograding experiment. Two different graders (PerCriterionOneShotGrader and PerCriterionGrader) evaluated two different answers (GOLDEN and MID) on a medical rubric about postpartum TMA/TTP diagnosis.

Here are the results:

{results_summary}

Please analyze:
1. What patterns do you see in the scores?
2. Are there significant differences between the two graders?
3. Is there any drift or inconsistency across the 5 runs for each combination?
4. What might explain the differences in how the graders scored the GOLDEN vs MID answers?
5. Any concerning patterns or insights about grader reliability?

Be specific, quantitative, and insightful."""

    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    
    return response.choices[0].message.content

async def main():
    # Prepare rubric
    criteria_list = []
    for section in rubric_raw["rubric"]["sections"]:
        criteria_list.extend(section["criteria"])

    rubric_json = json.dumps(criteria_list)
    rubric = Rubric.from_json(rubric_json)

    # Define test combinations
    test_configs = [
        ("PerCriterionOneShotGrader", "GOLDEN", PerCriterionOneShotGrader, GOLDEN_ANSWER),
        ("PerCriterionOneShotGrader", "MID", PerCriterionOneShotGrader, MID_ANSWER),
        ("PerCriterionGrader", "GOLDEN", PerCriterionGrader, GOLDEN_ANSWER),
        ("PerCriterionGrader", "MID", PerCriterionGrader, MID_ANSWER),
    ]

    num_runs = 5

    print(f"Running {len(test_configs) * num_runs} tests in parallel...\n")
    
    # Create all tasks upfront
    all_tasks = []
    task_metadata = []
    
    for grader_name, answer_name, grader_class, answer in test_configs:
        for run in range(num_runs):
            grader = grader_class(generate_fn=default_generate_fn)
            task = run_single_test(rubric, grader, answer)
            all_tasks.append(task)
            task_metadata.append((grader_name, answer_name, run + 1))
    
    # Run all tests in parallel
    print(f"Executing all {len(all_tasks)} tests concurrently...")
    all_results = await asyncio.gather(*all_tasks)
    print("All tests completed!\n")
    
    # Organize results with full evaluation data
    results = {}
    for (grader_name, answer_name, run_num), result in zip(task_metadata, all_results):
        key = (grader_name, answer_name)
        if key not in results:
            results[key] = {"results": [], "scores": [], "average": 0}
        results[key]["results"].append(result)
        results[key]["scores"].append(result.score)
        print(f"{grader_name} + {answer_name} [Run {run_num}]: {result.score:.2f}")
    
    # Calculate averages
    for key in results:
        results[key]["average"] = sum(results[key]["scores"]) / len(results[key]["scores"])

    # Build markdown report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"scripts/evaluation_report_{timestamp}.md"
    
    markdown_content = f"""# Autograder Evaluation Report
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Summary

### Results Matrix (Average Scores over {num_runs} runs)

| Grader | GOLDEN | MID |
|--------|--------|-----|
"""
    
    for grader_name in ["PerCriterionOneShotGrader", "PerCriterionGrader"]:
        golden_avg = results[(grader_name, "GOLDEN")]["average"]
        mid_avg = results[(grader_name, "MID")]["average"]
        markdown_content += f"| {grader_name} | {golden_avg:.2f} | {mid_avg:.2f} |\n"
    
    markdown_content += "\n## Detailed Results\n\n"
    
    # Add detailed breakdown for each combination
    for (grader_name, answer_name), data in results.items():
        markdown_content += f"### {grader_name} + {answer_name}\n\n"
        markdown_content += f"**Statistics:**\n"
        markdown_content += f"- Average: {data['average']:.2f}\n"
        markdown_content += f"- Min: {min(data['scores']):.2f}\n"
        markdown_content += f"- Max: {max(data['scores']):.2f}\n"
        std_dev = (sum((s - data['average'])**2 for s in data['scores']) / len(data['scores']))**0.5
        markdown_content += f"- Std Dev: {std_dev:.2f}\n"
        markdown_content += f"- Individual Scores: {[f'{s:.2f}' for s in data['scores']]}\n\n"
        
        # Add criterion-level details for each run
        for run_idx, result in enumerate(data["results"], 1):
            markdown_content += f"#### Run {run_idx} (Score: {result.score:.2f})\n\n"
            if result.report:
                markdown_content += "| Requirement | Weight | Verdict | Reason |\n"
                markdown_content += "|-------------|--------|---------|--------|\n"
                for crit_report in result.report:
                    # Truncate requirement and reason for table readability
                    req_short = crit_report.requirement[:60] + "..." if len(crit_report.requirement) > 60 else crit_report.requirement
                    reason_short = crit_report.reason[:80] + "..." if len(crit_report.reason) > 80 else crit_report.reason
                    markdown_content += f"| {req_short} | {crit_report.weight} | {crit_report.verdict} | {reason_short} |\n"
                markdown_content += "\n"
            else:
                markdown_content += "*No criterion-level details available*\n\n"
    
    # Create summary for GPT analysis
    results_summary = ""
    for (grader_name, answer_name), data in results.items():
        results_summary += f"\n{grader_name} + {answer_name}:\n"
        results_summary += f"  Scores: {data['scores']}\n"
        results_summary += f"  Average: {data['average']:.2f}\n"
        std_dev = (sum((s - data['average'])**2 for s in data['scores']) / len(data['scores']))**0.5
        results_summary += f"  Std Dev: {std_dev:.2f}\n"
    
    print("\nGenerating GPT analysis...")
    gpt_analysis = await analyze_results_with_gpt(results_summary)
    
    markdown_content += "\n---\n\n## AI Analysis\n\n"
    markdown_content += gpt_analysis + "\n"
    
    # Write to file
    with open(filename, 'w') as f:
        f.write(markdown_content)
    
    print(f"\n✅ Report written to: {filename}")
    print(f"\n{'='*70}")
    print("QUICK SUMMARY")
    print(f"{'='*70}")
    for grader_name in ["PerCriterionOneShotGrader", "PerCriterionGrader"]:
        golden_avg = results[(grader_name, "GOLDEN")]["average"]
        mid_avg = results[(grader_name, "MID")]["average"]
        print(f"{grader_name:<35} | GOLDEN: {golden_avg:>6.2f} | MID: {mid_avg:>6.2f}")
    print(f"{'='*70}")

if __name__ == "__main__":
    asyncio.run(main())