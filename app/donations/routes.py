from datetime import date
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.decorators import login_required, admin_required
from app.extensions import get_supabase_admin

donations_bp = Blueprint('donations', __name__)


@donations_bp.route('/')
@login_required
def list_donations():
    supabase = get_supabase_admin()

    status_filter     = request.args.get('status', '').strip()
    blood_group_filter = request.args.get('blood_group', '').strip()
    date_from         = request.args.get('date_from', '').strip()
    date_to           = request.args.get('date_to', '').strip()

    query = supabase.table('donations').select(
        '*, donors(full_name, blood_group, phone)'
    ).order('donation_date', desc=True)

    if status_filter:
        query = query.eq('status', status_filter)
    if blood_group_filter:
        query = query.eq('blood_group', blood_group_filter)
    if date_from:
        query = query.gte('donation_date', date_from)
    if date_to:
        query = query.lte('donation_date', date_to)

    res = query.execute()
    donations = res.data or []

    return render_template('donations/list.html',
        donations=donations,
        blood_groups=['A+','A-','B+','B-','O+','O-','AB+','AB-'],
        status_filter=status_filter,
        blood_group_filter=blood_group_filter,
        date_from=date_from,
        date_to=date_to,
    )


@donations_bp.route('/new', methods=['GET', 'POST'])
@admin_required
def new_donation():
    supabase = get_supabase_admin()

    # Pre-select donor if passed in query string
    preselect_donor_id = request.args.get('donor_id', '').strip()
    preselect_donor = None
    if preselect_donor_id:
        try:
            res = supabase.table('donors').select('*').eq('id', preselect_donor_id).single().execute()
            preselect_donor = res.data
        except Exception:
            pass

    if request.method == 'POST':
        donor_id = request.form.get('donor_id', '').strip()
        data = {
            'donor_id':         donor_id,
            'donation_date':    request.form.get('donation_date', '').strip(),
            'blood_group':      request.form.get('blood_group', '').strip(),
            'units_donated':    float(request.form.get('units_donated', 1.0)),
            'donation_center':  request.form.get('donation_center', '').strip() or None,
            'hemoglobin_level': float(request.form.get('hemoglobin_level')) if request.form.get('hemoglobin_level') else None,
            'blood_pressure':   request.form.get('blood_pressure', '').strip() or None,
            'status':           request.form.get('status', 'completed'),
            'notes':            request.form.get('notes', '').strip() or None,
            'recorded_by':      session['user']['id'],
        }

        if not all([data['donor_id'], data['donation_date'], data['blood_group']]):
            flash('Donor, donation date, and blood group are required.', 'danger')
            return render_template('donations/form.html',
                blood_groups=['A+','A-','B+','B-','O+','O-','AB+','AB-'],
                preselect_donor=preselect_donor, today=date.today().isoformat())

        try:
            # Check eligibility before inserting
            donor_res = supabase.table('donors').select('is_eligible, last_donation_date').eq('id', donor_id).single().execute()
            donor_info = donor_res.data
            
            if not donor_info.get('is_eligible', True):
                flash('This donor is currently marked as ineligible to donate.', 'danger')
                return redirect(url_for('donations.new_donation', donor_id=donor_id))
            
            if donor_info.get('last_donation_date'):
                last_don = date.fromisoformat(donor_info['last_donation_date'])
                if (date.fromisoformat(data['donation_date']) - last_don).days < 56:
                    flash('Donor has donated within the last 56 days and is not yet eligible.', 'danger')
                    return redirect(url_for('donations.new_donation', donor_id=donor_id))

            # Insert donation
            supabase.table('donations').insert(data).execute()

            if data['status'] == 'completed':
                # Update donor's last_donation_date and total_donations
                donor_res = supabase.table('donors').select('total_donations').eq('id', donor_id).single().execute()
                current_count = donor_res.data.get('total_donations', 0) or 0
                supabase.table('donors').update({
                    'last_donation_date': data['donation_date'],
                    'total_donations':    current_count + 1,
                }).eq('id', donor_id).execute()

                # Update blood inventory
                inv_res = supabase.table('blood_inventory').select('units_available').eq('blood_group', data['blood_group']).single().execute()
                current_units = inv_res.data.get('units_available', 0) or 0
                supabase.table('blood_inventory').update({
                    'units_available': float(current_units) + data['units_donated'],
                    'last_updated':    data['donation_date'],
                }).eq('blood_group', data['blood_group']).execute()

            flash('Donation recorded successfully.', 'success')
            return redirect(url_for('donations.list_donations'))

        except Exception as e:
            flash(f'Error recording donation: {str(e)}', 'danger')

    return render_template('donations/form.html',
        blood_groups=['A+','A-','B+','B-','O+','O-','AB+','AB-'],
        preselect_donor=preselect_donor,
        today=date.today().isoformat(),
    )


@donations_bp.route('/<donation_id>/delete', methods=['POST'])
@admin_required
def delete_donation(donation_id):
    try:
        supabase = get_supabase_admin()
        supabase.table('donations').delete().eq('id', donation_id).execute()
        flash('Donation record deleted.', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
    return redirect(url_for('donations.list_donations'))
