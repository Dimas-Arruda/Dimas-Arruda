# scripts/update_stats.py
import os
import requests
from collections import defaultdict
import json

# Common programming language colors for the SVG
# Source: https://github.com/ozh/github-colors/blob/master/colors.json
LANG_COLORS = {
    "Python": "#3572A5",
    "JavaScript": "#f1e05a",
    "TypeScript": "#2b7489",
    "HTML": "#e34c26",
    "CSS": "#563d7c",
    "Shell": "#89e051",
    "Java": "#b07219",
    "C++": "#f34b7d",
    "C": "#555555",
    "PHP": "#4F5D95",
    "Go": "#00ADD8",
    "Ruby": "#701516",
    "Jupyter Notebook": "#DA5B0B",
    "Default": "#888888"
}

def get_user_repos(username, token):
    """Fetches all public repositories for a given user, handling pagination."""
    repos = []
    page = 1
    while True:
        url = f"https://api.github.com/users/{username}/repos?page={page}&per_page=100"
        headers = {'Authorization': f'token {token}'}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        if not data:
            break
        repos.extend(data)
        page += 1
    return repos

def get_repo_languages(repo_full_name, token):
    """Fetches language data for a specific repository."""
    url = f"https://api.github.com/repos/{repo_full_name}/languages"
    headers = {'Authorization': f'token {token}'}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

def aggregate_languages(repos, username, token):
    """Aggregates language data across all non-forked repositories."""
    lang_stats = defaultdict(int)
    for repo in repos:
        if repo['fork']:
            continue
        try:
            languages = get_repo_languages(repo['full_name'], token)
            for lang, bytes_count in languages.items():
                lang_stats[lang] += bytes_count
        except requests.exceptions.HTTPError as e:
            # Silently ignore 404s for languages, can happen on empty repos
            if e.response.status_code != 404:
                print(f"Warning: Could not fetch languages for {repo['full_name']}: {e}")
    return lang_stats

def generate_svg(lang_stats, top_n=6):
    """Generates an SVG image from the top N language statistics."""
    if not lang_stats:
        return '<svg width="300" height="50"><text x="10" y="20">No language data found.</text></svg>'

    total_bytes = sum(lang_stats.values())
    sorted_langs = sorted(lang_stats.items(), key=lambda item: item[1], reverse=True)[:top_n]

    # SVG dimensions
    width = 300
    height = 50 + (len(sorted_langs) * 25)
    
    # SVG Header
    svg_content = f"""
    <svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
        <style>
            .header {{ font: 600 18px 'Segoe UI', Ubuntu, Sans-Serif; fill: #2f80ed; }}
            .lang-name {{ font: 400 14px 'Segoe UI', Ubuntu, Sans-Serif; fill: #333; }}
        </style>
        <rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="4.5" fill="#fff" stroke="#e4e2e2"/>
        <text x="15" y="35" class="header">Most Used Languages</text>
        <g transform="translate(0, 55)">
    """

    # Language items
    y_pos = 10
    for lang, bytes_count in sorted_langs:
        percentage = (bytes_count / total_bytes) * 100 if total_bytes > 0 else 0
        color = LANG_COLORS.get(lang, LANG_COLORS["Default"])
        
        svg_content += f"""
            <g transform="translate(15, {y_pos})">
                <circle cx="5" cy="6" r="5" fill="{color}"/>
                <text x="15" y="10" class="lang-name">{lang} ({percentage:.1f}%)</text>
            </g>
        """
        y_pos += 25

    svg_content += """
        </g>
    </svg>
    """
    return svg_content.strip()

def main():
    """Main function to run the script."""
    try:
        github_token = os.environ['GITHUB_TOKEN']
        github_repository = os.environ['GITHUB_REPOSITORY']
        username = github_repository.split('/')[0]

        print("Fetching user repositories...")
        repos = get_user_repos(username, github_token)
        
        print(f"Found {len(repos)} repositories. Aggregating language stats...")
        lang_stats = aggregate_languages(repos, username, github_token)
        
        print("Generating SVG image...")
        svg_image = generate_svg(lang_stats)
        
        # Ensure 'images' directory exists
        os.makedirs('images', exist_ok=True)
        
        output_path = 'images/top-langs-custom.svg'
        print(f"Saving SVG to {output_path}...")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(svg_image)
            
        print("Script finished successfully!")

    except Exception as e:
        print(f"An error occurred: {e}")
        exit(1)

if __name__ == "__main__":
    main()
