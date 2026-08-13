"""AI OS Bridge correlation record tests (§5.29): dedupe, lifecycle, boundary."""

from atoz_automation_service.errors import NotFoundError, ValidationError

from .fixtures import build_service, scenario


async def _make_service():
    _, service, _, captured = await build_service()
    return service, captured


async def _niche(service, slug="bridge-niche"):
    return await service.create_niche(name="Bridge Niche", slug=slug, status="active")


def test_create_aios_job_requires_niche() -> None:
    async def run():
        service, _ = await _make_service()
        try:
            await service.create_aios_job(niche_id="", job_id="j1", contract="AIOS.Content.Intake")
            raise AssertionError("expected ValidationError")
        except ValidationError:
            pass

    scenario(run)


def test_create_aios_job_is_idempotent_on_job_and_contract() -> None:
    async def run():
        service, captured = await _make_service()
        niche_id = (await _niche(service)).id
        first, created_first = await service.create_aios_job(
            niche_id=niche_id, job_id="job-42", contract="AIOS.Content.Intake"
        )
        second, created_second = await service.create_aios_job(
            niche_id=niche_id, job_id="job-42", contract="AIOS.Content.Intake"
        )
        assert created_first is True
        assert created_second is False
        assert second.id == first.id
        assert first.status == "pending"
        assert any(e.type == "automation:aios-job-created.v1" for e in captured)

    scenario(run)


def test_aios_job_lifecycle_transitions() -> None:
    async def run():
        service, _ = await _make_service()
        niche_id = (await _niche(service)).id
        row, _ = await service.create_aios_job(
            niche_id=niche_id, job_id="job-7", contract="AIOS.Pinterest.Assets"
        )
        in_progress = await service.set_aios_job_status(
            niche_id=niche_id,
            job_id="job-7",
            contract="AIOS.Pinterest.Assets",
            status="in_progress",
        )
        assert in_progress.status == "in_progress"
        done = await service.set_aios_job_status(
            niche_id=niche_id,
            job_id="job-7",
            contract="AIOS.Pinterest.Assets",
            status="succeeded",
        )
        assert done.status == "succeeded"
        assert done.completed_at is not None
        # Terminal states cannot be re-advanced.
        try:
            await service.set_aios_job_status(
                niche_id=niche_id,
                job_id="job-7",
                contract="AIOS.Pinterest.Assets",
                status="in_progress",
            )
            raise AssertionError("expected ValidationError")
        except ValidationError:
            pass

    scenario(run)


def test_aios_job_failure_increments_attempts() -> None:
    async def run():
        service, _ = await _make_service()
        niche_id = (await _niche(service)).id
        await service.create_aios_job(
            niche_id=niche_id, job_id="job-9", contract="AIOS.SEO.Metadata"
        )
        await service.set_aios_job_status(
            niche_id=niche_id, job_id="job-9", contract="AIOS.SEO.Metadata", status="in_progress"
        )
        failed = await service.set_aios_job_status(
            niche_id=niche_id,
            job_id="job-9",
            contract="AIOS.SEO.Metadata",
            status="failed",
            error="upstream timeout",
        )
        assert failed.status == "failed"
        assert failed.attempts == 1
        assert failed.error == "upstream timeout"

    scenario(run)


def test_aios_job_records_store_no_ai_internals() -> None:
    """Boundary: records carry correlation metadata only — never prompts or
    generated-content internals (Database Blueprint §5.29)."""

    async def run():
        from atoz_automation_service.domain.entities import AiosJobRecord

        service, _ = await _make_service()
        niche_id = (await _niche(service)).id
        row, _ = await service.create_aios_job(
            niche_id=niche_id,
            job_id="job-boundary",
            contract="AIOS.Content.Intake",
            payload_ref="s3://atoz-bucket/payloads/job-boundary.json",
        )
        columns = {c.name for c in AiosJobRecord.__table__.columns}
        assert "job_id" in columns
        assert "contract" in columns
        assert "payload_ref" in columns
        assert not {"prompt", "model_output", "generated_content", "embeddings"} & columns
        assert row.payload_ref is not None
        assert row.payload_ref.startswith("s3://")

    scenario(run)


def test_aios_job_cross_niche_access_blocked() -> None:
    async def run():
        service, _ = await _make_service()
        niche_a = await _niche(service, "aios-a")
        niche_b = await _niche(service, "aios-b")
        await service.create_aios_job(
            niche_id=niche_a.id, job_id="job-x", contract="AIOS.Content.Intake"
        )
        rows_a = await service.list_aios_jobs(niche_a.id)
        rows_b = await service.list_aios_jobs(niche_b.id)
        assert len(rows_a) == 1
        assert rows_b == []
        try:
            await service.set_aios_job_status(
                niche_id=niche_b.id,
                job_id="job-x",
                contract="AIOS.Content.Intake",
                status="in_progress",
            )
            raise AssertionError("expected NotFoundError cross-niche")
        except NotFoundError:
            pass

    scenario(run)
