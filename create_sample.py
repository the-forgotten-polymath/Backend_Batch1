"""Create sample Excel file for testing."""
import pandas as pd

# Sample data with real profile URLs (public profiles)
data = {
    'RollNo': ['2021001', '2021002', '2021003', '2021004', '2021005'],
    'LeetCodeURL': [
        'https://leetcode.com/problemsolver',
        'https://leetcode.com/u/testuser',
        'N/A',
        'https://leetcode.com/discuss',
        'https://leetcode.com/explore'
    ],
    'CodeforcesURL': [
        'https://codeforces.com/profile/tourist',
        'N/A',
        'https://codeforces.com/profile/Benq',
        'https://codeforces.com/profile/Petr',
        'N/A'
    ],
    'LinkedInURL': [
        'https://linkedin.com/in/williamhgates',
        'https://linkedin.com/in/satyanadella',
        'N/A',
        'https://linkedin.com/in/jeffweiner08',
        'https://linkedin.com/in/reidhoffman'
    ],
    'GitHubURL': [
        'https://github.com/torvalds',
        'https://github.com/gvanrossum',
        'https://github.com/mojombo',
        'N/A',
        'https://github.com/defunkt'
    ]
}

# Create DataFrame
df = pd.DataFrame(data)

# Save to Excel
output_file = 'sample_candidates.xlsx'
df.to_excel(output_file, index=False)

print(f"✅ Sample Excel file created: {output_file}")
print(f"📊 Contains {len(df)} sample rows")
print("\nYou can now test the API with this file:")
print(f"  curl -X POST http://localhost:5000/enrich -F 'excel=@{output_file}' -o result.zip")
