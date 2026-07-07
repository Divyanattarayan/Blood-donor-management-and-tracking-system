from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.extensions import get_supabase

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user' in session:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        email    = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()

        if not email or not password:
            flash('Email and password are required.', 'danger')
            return render_template('auth/login.html')

        try:
            supabase = get_supabase()
            res = supabase.auth.sign_in_with_password({'email': email, 'password': password})

            user_id = res.user.id

            # Fetch profile (role, name, etc.)
            profile_res = supabase.table('profiles').select('*').eq('id', user_id).single().execute()
            profile = profile_res.data

            session['user'] = {
                'id':        user_id,
                'email':     email,
                'full_name': profile.get('full_name', email),
                'role':      profile.get('role', 'donor'),
                'access_token': res.session.access_token,
            }
            flash(f"Welcome back, {profile.get('full_name', email)}!", 'success')
            return redirect(url_for('dashboard.index'))

        except Exception as e:
            print(f"Login error detail: {e}")
            flash('Invalid email or password. Please try again.', 'danger')
            return render_template('auth/login.html')

    return render_template('auth/login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if 'user' in session:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email     = request.form.get('email', '').strip()
        phone     = request.form.get('phone', '').strip()
        password  = request.form.get('password', '').strip()
        confirm   = request.form.get('confirm_password', '').strip()

        if not all([full_name, email, password, confirm]):
            flash('All fields are required.', 'danger')
            return render_template('auth/register.html')

        if password != confirm:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/register.html')

        if len(password) < 8:
            flash('Password must be at least 8 characters.', 'danger')
            return render_template('auth/register.html')

        try:
            supabase = get_supabase()
            res = supabase.auth.sign_up({
                'email': email,
                'password': password,
                'options': {
                    'data': {
                        'full_name': full_name,
                        'phone':     phone,
                        'role':      'donor',
                    }
                }
            })

            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('auth.login'))

        except Exception as e:
            error_msg = str(e)
            if 'already registered' in error_msg.lower() or 'already exists' in error_msg.lower():
                flash('An account with this email already exists.', 'danger')
            else:
                flash(f'Registration failed: {error_msg}', 'danger')
            return render_template('auth/register.html')

    return render_template('auth/register.html')


@auth_bp.route('/logout')
def logout():
    try:
        supabase = get_supabase()
        supabase.auth.sign_out()
    except Exception:
        pass
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))
