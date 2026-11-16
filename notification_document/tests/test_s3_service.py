from services import s3_service


class FakeS3Client:
    def __init__(self):
        self.upload = None
        self.presign = None

    def upload_file(self, filename, bucket, key, ExtraArgs):
        self.upload = (filename, bucket, key, ExtraArgs)

    def generate_presigned_url(self, operation, Params, ExpiresIn):
        self.presign = (operation, Params, ExpiresIn)
        return "https://example.test/signed-document"


def test_upload_document_stores_private_pdf_and_returns_presigned_url(tmp_path, monkeypatch):
    pdf = tmp_path / "visit_summary_9.pdf"
    pdf.write_bytes(b"%PDF-test")
    client = FakeS3Client()

    monkeypatch.setattr(s3_service.settings, "DOCUMENTS_S3_BUCKET", "patient-docs")
    monkeypatch.setattr(s3_service.settings, "DOCUMENTS_S3_PREFIX", "patient-care/documents")
    monkeypatch.setattr(s3_service.settings, "DOCUMENTS_S3_ENCRYPTION", "AES256")
    monkeypatch.setattr(s3_service.settings, "DOCUMENTS_S3_KMS_KEY_ID", None)
    monkeypatch.setattr(s3_service.settings, "DOCUMENT_LINK_EXPIRY_SECONDS", 3600)
    monkeypatch.setattr(s3_service, "_s3_client", lambda: client)

    result = s3_service.upload_document(str(pdf), "visit-summaries", 9)

    assert result.url == "https://example.test/signed-document"
    assert result.object_key == "patient-care/documents/visit-summaries/9/visit_summary_9.pdf"
    assert result.expires_in_seconds == 3600
    assert client.upload[1:3] == ("patient-docs", result.object_key)
    assert client.upload[3]["ContentType"] == "application/pdf"
    assert client.upload[3]["ServerSideEncryption"] == "AES256"
    assert client.presign[0] == "get_object"
    assert client.presign[1]["Bucket"] == "patient-docs"
    assert client.presign[2] == 3600


def test_upload_document_requires_a_bucket(tmp_path, monkeypatch):
    pdf = tmp_path / "document.pdf"
    pdf.write_bytes(b"%PDF-test")
    monkeypatch.setattr(s3_service.settings, "DOCUMENTS_S3_BUCKET", None)

    try:
        s3_service.upload_document(str(pdf), "prescriptions", 2)
    except s3_service.DocumentStorageError as exc:
        assert "DOCUMENTS_S3_BUCKET" in str(exc)
    else:
        raise AssertionError("Expected a missing-bucket error")
