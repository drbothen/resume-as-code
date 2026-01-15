# VHS Demo: Resume Plan Command
# Demonstrates AI-powered work unit selection

Output demo-plan.gif

Set FontSize 14
Set Width 1200
Set Height 800
Set Theme "Catppuccin Mocha"
Set Padding 20

Type "# Step 1: View your Work Units"
Enter
Sleep 500ms

Type "uv run resume list"
Enter
Sleep 3s

Enter
Type "# Step 2: Check the Job Description"
Enter
Sleep 500ms

Type "cat tests/fixtures/job_descriptions/senior_engineer.txt"
Enter
Sleep 4s

Enter
Type "# Step 3: Run the Plan to see AI-selected matches"
Enter
Sleep 500ms

Type "uv run resume plan --jd tests/fixtures/job_descriptions/senior_engineer.txt | less -R"
Enter
Sleep 3s

PageDown
Sleep 2s

PageDown
Sleep 2s

PageDown
Sleep 2s

Type "q"
Sleep 500ms

Enter
Type "# Plan shows relevance scores, skill matches, and coverage analysis!"
Enter
Sleep 2s
