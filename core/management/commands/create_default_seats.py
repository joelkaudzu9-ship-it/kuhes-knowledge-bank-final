from django.core.management.base import BaseCommand
from core.models import ModeratorSeat, User


class Command(BaseCommand):
    help = 'Create default moderator seats for all programs and years'

    def handle(self, *args, **options):
        self.stdout.write('Creating default moderator seats...')

        # ===========================================
        # PRE-MED SEATS (2 class reps + 6 subject leads)
        # ===========================================

        # Pre-Med Class Reps (2 seats)
        ModeratorSeat.objects.get_or_create(
            seat_code='PM-CR-1',
            defaults={
                'name': 'Pre-Med Class Representative 1',
                'seat_type': 'class_rep',
                'level': 'premed',
                'programme': 'Pre-Med',
                'programme_code': 'PM',
            }
        )

        ModeratorSeat.objects.get_or_create(
            seat_code='PM-CR-2',
            defaults={
                'name': 'Pre-Med Class Representative 2',
                'seat_type': 'assistant',
                'level': 'premed',
                'programme': 'Pre-Med',
                'programme_code': 'PM',
            }
        )

        # Pre-Med Subject Leads (6 seats)
        subjects = [
            ('BIO', 'biology', '🧬 Biology'),
            ('CHEM', 'chemistry', '🧪 Chemistry'),
            ('PHY', 'physics', '⚡ Physics'),
            ('MATH', 'mathematics', '📐 Mathematics'),
            ('ICT', 'ict', '💻 ICT'),
            ('COM', 'communication', '🗣️ Communication'),
        ]

        for code, subject, name in subjects:
            ModeratorSeat.objects.get_or_create(
                seat_code=f'PM-{code}-LEAD',
                defaults={
                    'name': f'Pre-Med {name} Lead',
                    'seat_type': 'subject_lead',
                    'level': 'premed',
                    'programme': 'Pre-Med',
                    'programme_code': 'PM',
                    'subject': subject,
                }
            )

        self.stdout.write(self.style.SUCCESS('✅ Pre-Med seats created'))

        # ===========================================
        # UNDERGRADUATE PROGRAMS
        # ===========================================

        programs = [
            # School of Medicine
            ('MED', 'medicine', 'MBBS', 5),
            ('MED', 'medicine', 'BDS', 5),

            # School of Nursing
            ('NUR', 'nursing', 'BNS', 4),
            ('NUR', 'nursing', 'BSc Mental Health', 4),

            # School of Maternal Health
            ('MAT', 'maternal', 'BSc Midwifery', 4),
            ('MAT', 'maternal', 'BSc Neonatal Health', 4),

            # School of Life Sciences
            ('LSC', 'life_sciences', 'BPharm', 4),
            ('LSC', 'life_sciences', 'BSc Physiotherapy', 4),
            ('LSC', 'life_sciences', 'BSc Occupational Therapy', 4),
            ('LSC', 'life_sciences', 'BSc Medical Lab Sciences', 4),
            ('LSC', 'life_sciences', 'BSc Biomedical Sciences', 4),

            # School of Public Health
            ('PUB', 'public_health', 'BSc Public Health', 4),
            ('PUB', 'public_health', 'BSc Environmental Health', 4),
        ]

        for prog_code, school, programme, max_years in programs:
            for year in range(1, max_years + 1):
                # Seat 1 (Class Rep)
                seat_code = f"{prog_code}-Y{year}-R1"
                ModeratorSeat.objects.get_or_create(
                    seat_code=seat_code,
                    defaults={
                        'name': f'{programme} Year {year} Representative 1',
                        'seat_type': 'class_rep',
                        'level': 'undergraduate',
                        'school': school,
                        'programme': programme,
                        'programme_code': prog_code,
                        'year': year,
                    }
                )

                # Seat 2 (Assistant Rep)
                seat_code = f"{prog_code}-Y{year}-R2"
                ModeratorSeat.objects.get_or_create(
                    seat_code=seat_code,
                    defaults={
                        'name': f'{programme} Year {year} Representative 2',
                        'seat_type': 'assistant',
                        'level': 'undergraduate',
                        'school': school,
                        'programme': programme,
                        'programme_code': prog_code,
                        'year': year,
                    }
                )

                self.stdout.write(f"  Created seats for {programme} Year {year}")

        # ===========================================
        # POSTGRADUATE PROGRAMS
        # ===========================================

        postgrad_programs = [
            ('MMED', 'MMED Surgery', 4),
            ('MMED', 'MMED Internal Medicine', 4),
            ('MMED', 'MMED Paediatrics', 4),
            ('MSC', 'MSc Clinical Research', 2),
            ('PHD', 'PhD Health Sciences', 3),
        ]

        for prog_code, programme, max_years in postgrad_programs:
            for year in range(1, max_years + 1):
                # Only one rep per postgraduate class
                seat_code = f"{prog_code}-Y{year}-REP"
                ModeratorSeat.objects.get_or_create(
                    seat_code=seat_code,
                    defaults={
                        'name': f'{programme} Year {year} Representative',
                        'seat_type': 'class_rep',
                        'level': 'postgraduate',
                        'programme': programme,
                        'programme_code': prog_code,
                        'year': year,
                    }
                )

        self.stdout.write(self.style.SUCCESS('✅ Undergraduate & Postgraduate seats created'))

        # ===========================================
        # DIPLOMA PROGRAMS
        # ===========================================

        diploma_programs = [
            ('DCM', 'Diploma in Clinical Medicine', 3),
            ('DNR', 'Diploma in Nursing', 3),
            ('DMLS', 'Diploma in Medical Lab Sciences', 3),
        ]

        for prog_code, programme, max_years in diploma_programs:
            for year in range(1, max_years + 1):
                seat_code = f"{prog_code}-Y{year}-REP"
                ModeratorSeat.objects.get_or_create(
                    seat_code=seat_code,
                    defaults={
                        'name': f'{programme} Year {year} Representative',
                        'seat_type': 'class_rep',
                        'level': 'diploma',
                        'programme': programme,
                        'programme_code': prog_code,
                        'year': year,
                    }
                )

        self.stdout.write(self.style.SUCCESS('✅ Diploma seats created'))

        # Summary
        total = ModeratorSeat.objects.count()
        vacant = ModeratorSeat.objects.filter(current_holder__isnull=True).count()
        filled = total - vacant

        self.stdout.write('=' * 50)
        self.stdout.write(self.style.SUCCESS(f'🎉 TOTAL SEATS CREATED: {total}'))
        self.stdout.write(f'   Filled: {filled}')
        self.stdout.write(f'   Vacant: {vacant}')
        self.stdout.write('=' * 50)