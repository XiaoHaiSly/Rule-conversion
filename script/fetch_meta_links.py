import os
import requests

REPO = "MetaCubeX/meta-rules-dat"
BRANCH = "meta"
TARGET_DIRS = ("geosite", "geoip")

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "..", "links", "links-meta.txt")

HEADERS = {"User-Agent": "Mozilla/5.0", "Accept": "application/vnd.github+json"}
_token = os.environ.get("GITHUB_TOKEN")
if _token:
    HEADERS["Authorization"] = f"token {_token}"


def get_branch_sha():
    url = f"https://api.github.com/repos/{REPO}/branches/{BRANCH}"
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return resp.json()["commit"]["sha"]


def get_tree(sha):
    """非递归拿某一层目录的直接内容，不会有整仓库那种截断问题。"""
    url = f"https://api.github.com/repos/{REPO}/git/trees/{sha}"
    resp = requests.get(url, headers=HEADERS, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    if data.get("truncated"):
        print(f"[警告] {url} 返回仍被截断了")
    return data.get("tree", [])


def find_child_sha(tree_items, name):
    for item in tree_items:
        if item.get("path") == name and item.get("type") == "tree":
            return item.get("sha")
    return None


def main():
    branch_sha = get_branch_sha()
    root_tree = get_tree(branch_sha)

    geo_sha = find_child_sha(root_tree, "geo")
    if not geo_sha:
        raise RuntimeError("仓库根目录下没找到 geo 目录，仓库结构可能变了，需要人工检查")

    geo_tree = get_tree(geo_sha)

    lines = []
    for dirname in TARGET_DIRS:
        sub_sha = find_child_sha(geo_tree, dirname)
        if not sub_sha:
            print(f"[警告] geo/{dirname} 目录没找到")
            continue

        sub_tree = get_tree(sub_sha)
        cnt = 0
        for item in sub_tree:
            if item.get("type") != "blob":
                continue
            fname = item.get("path", "")
            if not fname.lower().endswith((".yaml", ".yml")):
                continue
            name = fname.rsplit(".", 1)[0]
            raw_url = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/geo/{dirname}/{fname}"
            lines.append(f"{name} {raw_url}")
            cnt += 1
        print(f"[geo/{dirname}] 发现 {cnt} 个 yaml 文件")

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write("# 自动生成，来自 MetaCubeX/meta-rules-dat（geo/geosite + geo/geoip），请勿手动编辑\n")
        f.write("\n".join(lines) + "\n")

    print(f"共写入 {len(lines)} 条链接 -> {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
