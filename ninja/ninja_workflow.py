import yaml
import requests

# 1. 预处理：替换 ninja 节点为伪 ss 节点
def preprocess_ninja(input_file, temp_file):
    with open(input_file, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    proxies = data.get("proxies", [])
    new_proxies, ninja_backup = [], []

    for p in proxies:
        if p.get("type") == "ninja":
            ninja_backup.append(p)
            fake = {
                "name": p.get("name"),
                "type": "ss",
                "server": p.get("server"),
                "port": p.get("port"),
                "cipher": p.get("method", "aes-128-gcm"),
                "password": p.get("password", "fakepwd"),
                "udp": True
            }
            new_proxies.append(fake)
        else:
            new_proxies.append(p)

    data["proxies"] = new_proxies
    with open(temp_file, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False)

    return ninja_backup

# 2. 调用 Subconverter API，支持 config 参数
def call_subconverter(sub_url, target, urls, config=None):
    params = {"target": target, "url": "|".join(urls)}
    if config:
        params["config"] = config
    resp = requests.get(sub_url, params=params, timeout=30)
    resp.raise_for_status()
    return resp.text

# 3. 后处理：替换伪 ss 节点回 ninja 节点
def postprocess_ninja(clash_text, ninja_backup, output_file):
    parsed = yaml.safe_load(clash_text) or {}
    proxies = parsed.get("proxies", [])
    name_map = {n["name"]: n for n in ninja_backup}

    final_proxies = []
    for p in proxies:
        if p.get("type") == "ss" and p.get("name") in name_map:
            final_proxies.append(name_map[p["name"]])
        else:
            final_proxies.append(p)

    parsed["proxies"] = final_proxies
    with open(output_file, "w", encoding="utf-8") as f:
        yaml.safe_dump(parsed, f, allow_unicode=True, sort_keys=False)

    print(f">>> 已生成最终文件: {output_file}")

# 主流程
def main():
    input_file = "ninja.yaml"
    temp_file = "temp_fake.yaml"
    output_file = "final_with_ninja.yaml"

    # 1. 预处理
    ninja_backup = preprocess_ninja(input_file, temp_file)
    print(f">>> 已替换 {len(ninja_backup)} 个 ninja 节点为伪 ss 节点")

    # 2. 调用 Subconverter，带转换规则
    subconverter_url = "http://127.0.0.1:25500/sub"
    other_subs = ["http://127.0.0.1:5500/ninja/temp_fake.yaml"]  # 其它订阅 URL
    config_file = "https://raw.githubusercontent.com/Aethersailor/Custom_OpenClash_Rules/refs/heads/main/cfg/Custom_Clash_Full.ini"  # 外部转换规则文件

    clash_text = call_subconverter(subconverter_url, "clash", other_subs, config=config_file)

    # 3. 后处理
    postprocess_ninja(clash_text, ninja_backup, output_file)

if __name__ == "__main__":
    main()
