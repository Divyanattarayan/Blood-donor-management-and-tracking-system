import csv
import io
from collections import defaultdict
from flask import Blueprint, render_template, request, jsonify, Response
from app.decorators import admin_required
from app.extensions import get_supabase_admin

reports_bp = Blueprint('reports', __name__)


@reports_bp.route('/')
@admin_required
def index():
    supabase = get_supabase_admin()

    # Blood group distribution of donors
    donors_res = supabase.table('donors').select('blood_group').execute()
    bg_counts = defaultdict(int)
    for d in (donors_res.data or []):
        bg_counts[d['blood_group']] += 1

    # Monthly donation counts (last 12 months)
    donations_res = supabase.table('donations').select('donation_date, units_donated, status').eq('status', 'completed').execute()
    monthly = defaultdict(float)
    for d in (donations_res.data or []):
        key = d['donation_date'][:7]  # YYYY-MM
        monthly[key] += float(d.get('units_donated', 1))
    sorted_months = sorted(monthly.items())[-12:]

    # Current inventory
    inv_res = supabase.table('blood_inventory').select('*').order('blood_group').execute()
    inventory = inv_res.data or []

    # Top donors (by total_donations)
    top_donors_res = supabase.table('donors').select(
        'full_name, blood_group, total_donations, city'
    ).order('total_donations', desc=True).limit(10).execute()
    top_donors = top_donors_res.data or []

    return render_template('reports/index.html',
        bg_labels=list(bg_counts.keys()),
        bg_data=list(bg_counts.values()),
        monthly_labels=[m[0] for m in sorted_months],
        monthly_data=[m[1] for m in sorted_months],
        inventory=inventory,
        top_donors=top_donors,
    )


@reports_bp.route('/api/donations-by-month')
@admin_required
def api_donations_by_month():
    supabase = get_supabase_admin()
    res = supabase.table('donations').select('donation_date, units_donated').eq('status', 'completed').execute()
    monthly = defaultdict(float)
    for d in (res.data or []):
        key = d['donation_date'][:7]
        monthly[key] += float(d.get('units_donated', 1))
    sorted_months = sorted(monthly.items())[-12:]
    return jsonify({
        'labels': [m[0] for m in sorted_months],
        'data':   [m[1] for m in sorted_months],
    })


@reports_bp.route('/api/blood-group-distribution')
@admin_required
def api_blood_group_distribution():
    supabase = get_supabase_admin()
    res = supabase.table('donors').select('blood_group').execute()
    bg_counts = defaultdict(int)
    for d in (res.data or []):
        bg_counts[d['blood_group']] += 1
    return jsonify({'labels': list(bg_counts.keys()), 'data': list(bg_counts.values())})


@reports_bp.route('/api/inventory')
@admin_required
def api_inventory():
    supabase = get_supabase_admin()
    res = supabase.table('blood_inventory').select('*').order('blood_group').execute()
    return jsonify(res.data or [])


@reports_bp.route('/export/donors')
@admin_required
def export_donors():
    supabase = get_supabase_admin()
    res = supabase.table('donors').select('*').order('full_name').execute()
    donors = res.data or []

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=[
        'full_name', 'date_of_birth', 'gender', 'blood_group',
        'phone', 'email', 'city', 'state', 'is_eligible',
        'last_donation_date', 'total_donations', 'created_at'
    ])
    writer.writeheader()
    for donor in donors:
        writer.writerow({k: donor.get(k, '') for k in writer.fieldnames})

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=donors.csv'}
    )


@reports_bp.route('/export/donations')
@admin_required
def export_donations():
    supabase = get_supabase_admin()
    res = supabase.table('donations').select('*, donors(full_name, blood_group)').order('donation_date', desc=True).execute()
    donations = res.data or []

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Donor Name', 'Blood Group', 'Donation Date', 'Units', 'Center', 'Status', 'Notes'])
    for d in donations:
        donor_info = d.get('donors') or {}
        writer.writerow([
            donor_info.get('full_name', ''),
            d.get('blood_group', ''),
            d.get('donation_date', ''),
            d.get('units_donated', ''),
            d.get('donation_center', ''),
            d.get('status', ''),
            d.get('notes', ''),
        ])

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=donations.csv'}
    )
