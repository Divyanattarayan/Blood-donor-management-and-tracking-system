from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.decorators import login_required, admin_required
from app.extensions import get_supabase_admin

requests_bp = Blueprint('requests', __name__)

BLOOD_GROUPS = ['A+', 'A-', 'B+', 'B-', 'O+', 'O-', 'AB+', 'AB-']


@requests_bp.route('/')
@login_required
def list_requests():
    supabase = get_supabase_admin()

    status_filter  = request.args.get('status', '').strip()
    urgency_filter = request.args.get('urgency', '').strip()
    bg_filter      = request.args.get('blood_group', '').strip()

    query = supabase.table('blood_requests').select('*').order('created_at', desc=True)

    if status_filter:
        query = query.eq('status', status_filter)
    if urgency_filter:
        query = query.eq('urgency', urgency_filter)
    if bg_filter:
        query = query.eq('blood_group', bg_filter)

    res = query.execute()
    blood_requests = res.data or []

    return render_template('requests/list.html',
        blood_requests=blood_requests,
        blood_groups=BLOOD_GROUPS,
        status_filter=status_filter,
        urgency_filter=urgency_filter,
        bg_filter=bg_filter,
    )


@requests_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new_request():
    if request.method == 'POST':
        data = {
            'requester_name':   request.form.get('requester_name', '').strip(),
            'requester_phone':  request.form.get('requester_phone', '').strip(),
            'requester_email':  request.form.get('requester_email', '').strip() or None,
            'blood_group':      request.form.get('blood_group', '').strip(),
            'units_required':   int(request.form.get('units_required', 1)),
            'urgency':          request.form.get('urgency', 'normal'),
            'hospital_name':    request.form.get('hospital_name', '').strip() or None,
            'required_by_date': request.form.get('required_by_date', '').strip() or None,
            'notes':            request.form.get('notes', '').strip() or None,
            'requested_by':     session['user']['id'],
            'status':           'pending',
        }

        if not all([data['requester_name'], data['requester_phone'], data['blood_group']]):
            flash('Name, phone, and blood group are required.', 'danger')
            return render_template('requests/form.html', blood_groups=BLOOD_GROUPS, req=data)

        try:
            supabase = get_supabase_admin()
            supabase.table('blood_requests').insert(data).execute()
            flash('Blood request submitted successfully.', 'success')
            return redirect(url_for('requests.list_requests'))
        except Exception as e:
            flash(f'Error submitting request: {str(e)}', 'danger')

    return render_template('requests/form.html', blood_groups=BLOOD_GROUPS, req={})


@requests_bp.route('/<request_id>')
@login_required
def request_detail(request_id):
    supabase = get_supabase_admin()
    res = supabase.table('blood_requests').select('*').eq('id', request_id).single().execute()
    blood_request = res.data
    return render_template('requests/detail.html', blood_request=blood_request)


@requests_bp.route('/<request_id>/status', methods=['POST'])
@admin_required
def update_status(request_id):
    new_status   = request.form.get('status', 'pending')
    fulfilled_by = request.form.get('fulfilled_by', '').strip() or None

    try:
        supabase = get_supabase_admin()
        update_data = {'status': new_status}
        if fulfilled_by:
            update_data['fulfilled_by'] = fulfilled_by
        supabase.table('blood_requests').update(update_data).eq('id', request_id).execute()
        flash(f'Request status updated to {new_status}.', 'success')
    except Exception as e:
        flash(f'Error updating status: {str(e)}', 'danger')

    return redirect(url_for('requests.request_detail', request_id=request_id))


@requests_bp.route('/<request_id>/delete', methods=['POST'])
@admin_required
def delete_request(request_id):
    try:
        supabase = get_supabase_admin()
        supabase.table('blood_requests').delete().eq('id', request_id).execute()
        flash('Blood request deleted.', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
    return redirect(url_for('requests.list_requests'))
