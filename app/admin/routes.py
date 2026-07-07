from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.decorators import admin_required
from app.extensions import get_supabase_admin

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/')
@admin_required
def index():
    supabase = get_supabase_admin()

    users_res    = supabase.table('profiles').select('*').order('created_at', desc=True).execute()
    users        = users_res.data or []
    total_admins = sum(1 for u in users if u.get('role') == 'admin')
    total_donors = sum(1 for u in users if u.get('role') == 'donor')

    return render_template('admin/dashboard.html',
        users=users,
        total_admins=total_admins,
        total_donors_count=total_donors,
    )


@admin_bp.route('/users')
@admin_required
def users():
    supabase = get_supabase_admin()
    res = supabase.table('profiles').select('*').order('full_name').execute()
    all_users = res.data or []
    return render_template('admin/users.html', users=all_users)


@admin_bp.route('/users/<user_id>/role', methods=['POST'])
@admin_required
def update_role(user_id):
    new_role = request.form.get('role', 'donor')
    if new_role not in ('admin', 'donor'):
        flash('Invalid role.', 'danger')
        return redirect(url_for('admin.users'))
    try:
        supabase = get_supabase_admin()
        supabase.table('profiles').update({'role': new_role}).eq('id', user_id).execute()
        flash('User role updated.', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
    return redirect(url_for('admin.users'))


@admin_bp.route('/inventory')
@admin_required
def inventory():
    supabase = get_supabase_admin()
    res = supabase.table('blood_inventory').select('*').order('blood_group').execute()
    inventory = res.data or []
    return render_template('admin/inventory.html', inventory=inventory)


@admin_bp.route('/inventory/update', methods=['POST'])
@admin_required
def update_inventory():
    blood_group = request.form.get('blood_group', '').strip()
    units       = request.form.get('units_available', '').strip()

    if not blood_group or not units:
        flash('Blood group and units are required.', 'danger')
        return redirect(url_for('admin.inventory'))

    try:
        supabase = get_supabase_admin()
        supabase.table('blood_inventory').update({
            'units_available': float(units)
        }).eq('blood_group', blood_group).execute()
        flash(f'{blood_group} inventory updated to {units} units.', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')

    return redirect(url_for('admin.inventory'))
