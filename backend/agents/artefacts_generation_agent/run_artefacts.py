from pathlib import Path
from executor import ArtefactsAgentExecutor

def main():
    project_root = Path(__file__).resolve().parent.parent
    input_json = project_root / "outputs" / "requirements_output.json"
    output_dir = project_root / "outputs"

    executor = ArtefactsAgentExecutor(
        input_json=input_json,
        output_dir=output_dir
    )

    generated = executor.run(export_pdf=True)

    print("Generated artefacts:")
    for name, path in generated.items():
        print(f"- {name}: {path}")

if __name__ == "__main__":
    main()
