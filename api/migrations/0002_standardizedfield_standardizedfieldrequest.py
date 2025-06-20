# Generated by Django 4.1.7 on 2025-06-07 12:39

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='StandardizedField',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('field', models.CharField(blank=True, choices=[('location', 'Work Location'), ('other_certification', 'Assessment Certification'), ('area_of_expertise', 'Industry'), ('job_roles', 'Job roles'), ('companies_worked_in', 'Companies worked in'), ('language', 'Language Proficiency'), ('education', 'Education Institutions'), ('domain', 'Functional Domain'), ('client_companies', 'Client companies'), ('educational_qualification', 'Educational Qualification'), ('city', 'City'), ('country', 'Country'), ('topic', 'Topic'), ('product_type', 'Product Type'), ('category', 'Category'), ('asset_location', 'Location'), ('project_type', 'Project Type'), ('credentials_feels_like', 'Credential Feels like'), ('competency', 'Competency'), ('coaching_type', 'Coaching Type'), ('function', 'Function'), ('client_experience_level', 'Client Experience Level')], max_length=225)),
                ('values', models.JSONField(blank=True, default=list)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='StandardizedFieldRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.CharField(blank=True, max_length=255)),
                ('status', models.CharField(blank=True, choices=[('pending', 'Pending'), ('accepted', 'Accepted'), ('rejected', 'Rejected')], max_length=20)),
                ('requested_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('standardized_field_name', models.ForeignKey(blank=True, on_delete=django.db.models.deletion.CASCADE, to='api.standardizedfield')),
            ],
        ),
    ]
