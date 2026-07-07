from datetime import date, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from app.decorators import login_required, admin_required
from app.extensions import get_supabase_admin

donors_bp = Blueprint('donors', __name__)

BLOOD_GROUPS = ['A+', 'A-', 'B+', 'B-', 'O+', 'O-', 'AB+', 'AB-']
DONATION_GAP_DAYS = 56  # 8 weeks


@donors_bp.route('/')
@login_required
def list_donors():
    supabase = get_supabase_admin()
    query = supabase.table('donors').select('*').order('full_name')

    # Search filters
    search      = request.args.get('search', '').strip()
    blood_group = request.args.get('blood_group', '').strip()
    city        = request.args.get('city', '').strip()
    eligible    = request.args.get('eligible', '').strip()

    if blood_group:
        query = query.eq('blood_group', blood_group)
    if eligible == 'true':
        query = query.eq('is_eligible', True)
    elif eligible == 'false':
        query = query.eq('is_eligible', False)

    res = query.execute()
    donors = res.data or []

    # Client-side text filter for name/city (Supabase free tier has limited ilike)
    if search:
        search_lower = search.lower()
        donors = [d for d in donors if
                  search_lower in d.get('full_name', '').lower() or
                  search_lower in d.get('phone', '').lower() or
                  search_lower in d.get('email', '').lower()]
    if city:
        donors = [d for d in donors if city.lower() in d.get('city', '').lower()]

    return render_template('donors/list.html',
        donors=donors,
        blood_groups=BLOOD_GROUPS,
        search=search,
        selected_blood_group=blood_group,
        selected_city=city,
        selected_eligible=eligible,
    )


@donors_bp.route('/new', methods=['GET', 'POST'])
@admin_required
def new_donor():
    if request.method == 'POST':
        data = {
            'full_name':     request.form.get('full_name', '').strip(),
            'date_of_birth': request.form.get('date_of_birth', '').strip(),
            'gender':        request.form.get('gender', '').strip(),
            'blood_group':   request.form.get('blood_group', '').strip(),
            'phone':         request.form.get('phone', '').strip(),
            'email':         request.form.get('email', '').strip() or None,
            'address':       request.form.get('address', '').strip() or None,
            'city':          request.form.get('city', '').strip() or None,
            'state':         request.form.get('state', '').strip() or None,
            'is_eligible':   True,
        }

        if not all([data['full_name'], data['date_of_birth'], data['gender'],
                    data['blood_group'], data['phone']]):
            flash('Please fill in all required fields.', 'danger')
            return render_template('donors/form.html', blood_groups=BLOOD_GROUPS, donor=data)

        try:
            supabase = get_supabase_admin()
            supabase.table('donors').insert(data).execute()
            flash(f"Donor {data['full_name']} added successfully.", 'success')
            return redirect(url_for('donors.list_donors'))
        except Exception as e:
            flash(f'Error adding donor: {str(e)}', 'danger')

    return render_template('donors/form.html', blood_groups=BLOOD_GROUPS, donor={})


@donors_bp.route('/<donor_id>')
@login_required
def donor_detail(donor_id):
    supabase = get_supabase_admin()

    donor_res = supabase.table('donors').select('*').eq('id', donor_id).single().execute()
    donor = donor_res.data

    # Donation history
    donations_res = supabase.table('donations').select('*').eq('donor_id', donor_id).order('donation_date', desc=True).execute()
    donations = donations_res.data or []

    # Check eligibility (56-day rule)
    eligible = True
    next_eligible_date = None
    if donor.get('last_donation_date'):
        last = date.fromisoformat(donor['last_donation_date'])
        next_eligible = last + timedelta(days=DONATION_GAP_DAYS)
        if date.today() < next_eligible:
            eligible = False
            next_eligible_date = next_eligible.strftime('%d %b %Y')

    return render_template('donors/detail.html',
        donor=donor,
        donations=donations,
        eligible=eligible,
        next_eligible_date=next_eligible_date,
    )


@donors_bp.route('/<donor_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_donor(donor_id):
    supabase = get_supabase_admin()
    donor_res = supabase.table('donors').select('*').eq('id', donor_id).single().execute()
    donor = donor_res.data

    if request.method == 'POST':
        data = {
            'full_name':   request.form.get('full_name', '').strip(),
            'date_of_birth': request.form.get('date_of_birth', '').strip(),
            'gender':      request.form.get('gender', '').strip(),
            'blood_group': request.form.get('blood_group', '').strip(),
            'phone':       request.form.get('phone', '').strip(),
            'email':       request.form.get('email', '').strip() or None,
            'address':     request.form.get('address', '').strip() or None,
            'city':        request.form.get('city', '').strip() or None,
            'state':       request.form.get('state', '').strip() or None,
            'is_eligible': request.form.get('is_eligible') == 'true',
        }

        try:
            supabase.table('donors').update(data).eq('id', donor_id).execute()
            flash('Donor updated successfully.', 'success')
            return redirect(url_for('donors.donor_detail', donor_id=donor_id))
        except Exception as e:
            flash(f'Error updating donor: {str(e)}', 'danger')

    return render_template('donors/form.html',
        blood_groups=BLOOD_GROUPS,
        donor=donor,
        edit_mode=True,
    )


@donors_bp.route('/<donor_id>/delete', methods=['POST'])
@admin_required
def delete_donor(donor_id):
    try:
        supabase = get_supabase_admin()
        supabase.table('donors').delete().eq('id', donor_id).execute()
        flash('Donor deleted successfully.', 'success')
    except Exception as e:
        flash(f'Error deleting donor: {str(e)}', 'danger')
    return redirect(url_for('donors.list_donors'))


@donors_bp.route('/api/search')
@login_required
def api_search():
    supabase   = get_supabase_admin()
    blood_group = request.args.get('blood_group', '').strip()
    query = supabase.table('donors').select('id, full_name, blood_group, phone, city, is_eligible')
    if blood_group:
        query = query.eq('blood_group', blood_group).eq('is_eligible', True)
    res = query.limit(20).execute()
    return jsonify(res.data or [])
