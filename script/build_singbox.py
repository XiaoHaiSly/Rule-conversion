import os
import concurrent.futures
import tempfile

import common

# 手动维护的规则源（links-domain / links-ipcidr / links-mixed）
# 输出到 rules/singbox
RULES_LINKS_FILES = [
    "../links/links-domain.txt",
    "../links/links-ipcidr.txt",
    "../links/links-mixed.txt",
]
RULES_OUTPUT_ROOT = "../rules/singbox"

# 自动从 MetaCubeX/meta-rules-dat 拉取的全量 geosite+geoip（links-meta.txt）
# 输出到 geo-data/singbox，与手动维护的规则分开存放
GEO_LINKS_FILES = [
    "../links/links-meta.txt",
]
GEO_OUTPUT_ROOT = "../geo-data/singbox"


def write_domain(filtered, name, out_dir):
    if not filtered:
        return False
    os.makedirs(out_dir, exist_ok=True)
    json_path = os.path.join(out_dir, f"{name}_Domain.json")
    srs_path = os.path.join(out_dir, f"{name}_Domain.srs")
    common.unified_to_singbox_json(filtered, json_path)
    common.run(["sing-box", "rule-set", "compile", "--output", srs_path, json_path])
    return True


def write_ip(filtered, name, out_dir):
    if not filtered:
        return False
    os.makedirs(out_dir, exist_ok=True)
    json_path = os.path.join(out_dir, f"{name}_IP.json")
    srs_path = os.path.join(out_dir, f"{name}_IP.srs")
    common.unified_to_singbox_json(filtered, json_path)
    common.run(["sing-box", "rule-set", "compile", "--output", srs_path, json_path])
    return True


def build_one(name_link, work_dir, output_root):
    custom_name, link = name_link
    try:
        name, unified = common.link_to_unified(link, work_dir, custom_name)

        if unified == 'UNSUPPORTED':
            print(f"[跳过] {link}：mihomo 官方未提供 mrs 反解工具，srs 无法处理此输入")
            return
        if not unified:
            print(f"[跳过] {link}：未解析出任何规则")
            return

        domain_part, ipcidr_part, leftover = common.split_mixed_unified(unified)
        if leftover:
            print(f"[提示] {name}: 以下字段既不算域名也不算IP，已跳过: {leftover}")

        out_dir = os.path.join(output_root, name)
        wrote = []
        if write_domain(domain_part, name, out_dir):
            wrote.append("Domain")
        if write_ip(ipcidr_part, name, out_dir):
            wrote.append("IP")

        if wrote:
            print(f"[完成] {link} -> {output_root}/{name}/ ({','.join(wrote)})")
        else:
            print(f"[跳过] {link}：识别不出域名或IP规则")
    except Exception as e:
        print(f"[出错] {link} 处理失败，已跳过，原因：{e}")


def run_group(links_files, output_root, work_dir):
    os.makedirs(output_root, exist_ok=True)
    all_links = []
    for links_path in links_files:
        all_links.extend(common.read_links(links_path))

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        list(executor.map(lambda nl: build_one(nl, work_dir, output_root), all_links))


def main():
    with tempfile.TemporaryDirectory() as work_dir:
        run_group(RULES_LINKS_FILES, RULES_OUTPUT_ROOT, work_dir)
        run_group(GEO_LINKS_FILES, GEO_OUTPUT_ROOT, work_dir)


if __name__ == '__main__':
    main()
