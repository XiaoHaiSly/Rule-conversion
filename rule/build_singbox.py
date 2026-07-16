import os
import concurrent.futures
import tempfile

import common

CATEGORIES = [
    ("../links-domain.txt", "./singbox/domain", common.DOMAIN_FIELDS, "domain"),
    ("../links-ipcidr.txt", "./singbox/ipcidr", common.IPCIDR_FIELDS, "ipcidr"),
]


def build_one(name_link, work_dir, output_dir, keep_fields, category_label):
    custom_name, link = name_link
    try:
        name, unified = common.link_to_unified(link, work_dir, custom_name)

        if unified == 'UNSUPPORTED':
            print(f"[跳过] {link}：mihomo 官方未提供 mrs 反解工具，srs.yml 无法处理此输入")
            return
        if not unified:
            print(f"[跳过] {link}：未解析出任何规则")
            return

        filtered, dropped = common.filter_unified(unified, keep_fields)
        if dropped:
            print(f"[提示] {name} ({category_label}): 忽略了不属于此分类的字段 {dropped}，"
                  f"如需保留请把此链接也加进对应的 links-*.txt")
        if not filtered:
            print(f"[跳过] {link}：过滤后没有属于 {category_label} 分类的规则")
            return

        json_path = os.path.join(output_dir, f"{name}.json")
        srs_path = os.path.join(output_dir, f"{name}.srs")
        common.unified_to_singbox_json(filtered, json_path)
        common.run(["sing-box", "rule-set", "compile", "--output", srs_path, json_path])
        print(f"[完成] {link} -> singbox/{category_label}/{name}.json + .srs")
    except Exception as e:
        print(f"[出错] {link} 处理失败，已跳过，原因：{e}")


def main():
    with tempfile.TemporaryDirectory() as work_dir:
        for links_path, output_dir, keep_fields, category_label in CATEGORIES:
            os.makedirs(output_dir, exist_ok=True)
            links = common.read_links(links_path)
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                list(executor.map(
                    lambda nl: build_one(nl, work_dir, output_dir, keep_fields, category_label),
                    links
                ))


if __name__ == '__main__':
    main()
