from flask import Blueprint, render_template, session, jsonify
from app.decorators import login_required
from app.extensions import get_supabase_admin

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
@login_required
def index():
    supabase = get_supabase_admin()

    # Total donors
    donors_res = supabase.table('donors').select('id', count='exact').execute()
    total_donors = donors_res.count or 0

    # Total donations
    donations_res = supabase.table('donations').select('id', count='exact').execute()
    total_donations = donations_res.count or 0

    # Pending blood requests
    requests_res = supabase.table('blood_requests').select('id', count='exact').eq('status', 'pending').execute()
    pending_requests = requests_res.count or 0

    # Blood inventory
    inventory_res = supabase.table('blood_inventory').select('*').order('blood_group').execute()
    inventory = inventory_res.data or []

    # Recent donations (last 5)
    recent_donations_res = supabase.table('donations').select(
        '*, donors(full_name, blood_group)'
    ).order('donation_date', desc=True).limit(5).execute()
    recent_donations = recent_donations_res.data or []

    # Recent blood requests (last 5)
    recent_requests_res = supabase.table('blood_requests').select(
        '*'
    ).order('created_at', desc=True).limit(5).execute()
    recent_requests = recent_requests_res.data or []

    # Low stock alerts (< 5 units)
    low_stock = [item for item in inventory if item.get('units_available', 0) < 5]

    return render_template('dashboard/index.html',
        total_donors=total_donors,
        total_donations=total_donations,
        pending_requests=pending_requests,
        inventory=inventory,
        recent_donations=recent_donations,
        recent_requests=recent_requests,
        low_stock=low_stock,
    )


@dashboard_bp.route('/api/stats')
@login_required
def api_stats():
    supabase = get_supabase_admin()
    donors_res    = supabase.table('donors').select('id', count='exact').execute()
    donations_res = supabase.table('donations').select('id', count='exact').execute()
    requests_res  = supabase.table('blood_requests').select('id', count='exact').eq('status', 'pending').execute()
    inventory_res = supabase.table('blood_inventory').select('*').execute()

    return jsonify({
        'total_donors':    donors_res.count or 0,
        'total_donations': donations_res.count or 0,
        'pending_requests': requests_res.count or 0,
        'inventory': inventory_res.data or [],
    })
