import os
import requests

REPO = "MetaCubeX/meta-rules-dat"
BRANCH = "meta"
DIRS = ("geo/geosite/", "geo/geoip/")

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


def list_all_files():
    """用 Git Trees API（recursive=1）一次性拿整棵树，避免 Contents API 对大目录的截断问题。"""
    sha = get_branch_sha()
    url = f"https://api.github.com/repos/{REPO}/git/trees/{sha}?recursive=1"
    resp = requests.get(url, headers=HEADERS, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    if data.get("truncated"):
        print("[警告] GitHub 返回的目录树仍被截断了（超过单次树接口上限），部分文件可能抓不全")
    return data.get("tree", [])


def main():
    tree = list_all_files()

    lines = []
    counts = {d: 0 for d in DIRS}
    for item in tree:
        if item.get("type") != "blob":
            continue
        path = item.get("path", "")
        for d in DIRS:
            if not path.startswith(d):
                continue
            rest = path[len(d):]
            if "/" in rest:
                # 子目录里的文件不要
                continue
            if not rest.lower().endswith((".yaml", ".yml")):
                continue
            name = rest.rsplit(".", 1)[0]
            raw_url = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/{path}"
            lines.append(f"{name} {raw_url}")
            counts[d] += 1
            break

    for d, c in counts.items():
        print(f"[{d}] 发现 {c} 个 yaml 文件")

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write("# 自动生成，来自 MetaCubeX/meta-rules-dat（geo/geosite + geo/geoip），请勿手动编辑\n")
        f.write("\n".join(lines) + "\n")

    print(f"共写入 {len(lines)} 条链接 -> {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
