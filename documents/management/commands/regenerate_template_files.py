"""
Management command: regenerate_template_files
Finds documents that were created from a template and have placeholder_values
in metadata but are missing a generated file, then regenerates the file for each.
"""
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from documents.models import Document
from documents.office_utils import generate_document_from_template


class Command(BaseCommand):
    help = "Regenerate missing generated files for documents created from templates"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show which documents would be processed without generating files",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        # Find all template-linked docs that have placeholder data but no file
        candidates = Document.objects.filter(
            template__isnull=False,
            generated_file="",
        ).exclude(metadata={})

        docs_to_fix = [
            d for d in candidates if d.metadata.get("placeholder_values")
        ]

        if not docs_to_fix:
            self.stdout.write(self.style.SUCCESS("No documents need regeneration."))
            return

        self.stdout.write(
            f"Found {len(docs_to_fix)} document(s) that need file regeneration."
        )

        if dry_run:
            for doc in docs_to_fix:
                self.stdout.write(f"  [DRY-RUN] Would regenerate: [{doc.pk}] {doc.title}")
            return

        success_count = 0
        fail_count = 0

        for doc in docs_to_fix:
            template = doc.template
            if not template or not template.template_file:
                self.stdout.write(
                    self.style.WARNING(f"  [{doc.pk}] {doc.title} — template file missing, skipping")
                )
                fail_count += 1
                continue

            template_file_path = template.template_file.path
            if not os.path.exists(template_file_path):
                self.stdout.write(
                    self.style.WARNING(
                        f"  [{doc.pk}] {doc.title} — template file not found on disk ({template_file_path}), skipping"
                    )
                )
                fail_count += 1
                continue

            file_format = (template.file_format or "").lower()
            replacements = doc.metadata["placeholder_values"]

            # Build output path in MEDIA_ROOT/generated_documents/
            out_dir = os.path.join(settings.MEDIA_ROOT, "generated_documents")
            os.makedirs(out_dir, exist_ok=True)
            out_filename = f"doc_{doc.pk}_tpl{template.pk}.{file_format}"
            out_path = os.path.join(out_dir, out_filename)

            ok, err = generate_document_from_template(
                template_file_path, file_format, out_path, replacements
            )

            if ok and os.path.exists(out_path):
                # Save relative path (relative to MEDIA_ROOT)
                rel_path = os.path.relpath(out_path, settings.MEDIA_ROOT).replace("\\", "/")
                doc.generated_file = rel_path
                doc.save(update_fields=["generated_file"])
                self.stdout.write(
                    self.style.SUCCESS(f"  ✓ [{doc.pk}] {doc.title} → {rel_path}")
                )
                success_count += 1
            else:
                self.stdout.write(
                    self.style.ERROR(
                        f"  ✗ [{doc.pk}] {doc.title} — generation failed: {err}"
                    )
                )
                fail_count += 1

        self.stdout.write(
            f"\nDone: {success_count} regenerated, {fail_count} failed."
        )
