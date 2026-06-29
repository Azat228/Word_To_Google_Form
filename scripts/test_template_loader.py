from school_form_app.config.template_loader import load_test_configs


def main():
    configs = load_test_configs()

    print(f"Configs found: {len(configs)}")
    print()

    for config in configs:
        print("ID:", config.get("id"))
        print("Name:", config.get("name"))
        print("Parser type:", config.get("parser_type"))
        print("Thresholds:", len(config.get("thresholds", [])))
        print()


if __name__ == "__main__":
    main()