from __future__ import annotations

import os
from datetime import datetime

from django.apps import apps
from django.core.management.base import BaseCommand
from django.db import models


class Command(BaseCommand):
    help = "Generează un backup SQL cu INSERT-uri pentru tabelele proprii."

    def add_arguments(self, parser):
        parser.add_argument(
            "--output",
            default=None,
            help="Calea fișierului de backup (implicit: backups/backup_<timestamp>.sql)",
        )

    def handle(self, *args, **options):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = options["output"]
        if not output_path:
            os.makedirs("backups", exist_ok=True)
            output_path = os.path.join("backups", f"backup_{timestamp}.sql")

        models_to_dump = [
            m
            for m in apps.get_models()
            if not m._meta.app_label.startswith("auth")
            and not m._meta.app_label.startswith("admin")
            and not m._meta.app_label.startswith("contenttypes")
            and not m._meta.app_label.startswith("sessions")
        ]

        def format_value(val):
            if val is None:
                return "NULL"
            if isinstance(val, bool):
                return "1" if val else "0"
            if isinstance(val, (int, float)):
                return str(val)
            if isinstance(val, datetime):
                return f"'{val.isoformat(sep=' ')}'"
            if isinstance(val, models.Model):
                return str(getattr(val, "pk"))
            val_str = str(val).replace("'", "''")
            return f"'{val_str}'"

        lines = []
        for model in models_to_dump:
            table = model._meta.db_table
            fields = [
                f for f in model._meta.concrete_fields if not isinstance(f, models.AutoField)
            ]
            field_names = [f.column for f in fields]
            for obj in model.objects.all():
                values = [format_value(getattr(obj, f.attname)) for f in fields]
                line = f"INSERT INTO {table} ({', '.join(field_names)}) VALUES ({', '.join(values)});"
                lines.append(line)

        with open(output_path, "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines))

        self.stdout.write(self.style.SUCCESS(f"Backup salvat în {output_path}"))
