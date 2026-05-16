from worker.runner import VoxRunner, TtsRequest


def main() -> None:
    runner = VoxRunner(output_dir="artifacts")
    result = runner.generate_chapter(
        TtsRequest(
            job_id="sample-job",
            chapter_id="sample-chapter",
            text="Chapter One. Rain carried through the valley while the station lights flickered.",
        )
    )
    print(result)


if __name__ == "__main__":
    main()
