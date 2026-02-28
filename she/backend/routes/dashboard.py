from flask import render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from she.backend.models import User, Course, Job, Mentorship, Progress, db
from . import dashboard_bp

@dashboard_bp.route('/dashboard')
@login_required
def index():
    if current_user.role == 'women':
        courses = Course.query.limit(3).all()
        jobs = Job.query.filter_by(is_active=True).limit(3).all()
        mentors = User.query.filter_by(role='mentor').limit(3).all()
        progress = Progress.query.filter_by(user_id=current_user.id).all()
        return render_template('women_dashboard.html', 
                             courses=courses, 
                             jobs=jobs, 
                             mentors=mentors,
                             progress=progress)
    
    elif current_user.role == 'mentor':
        mentees = Mentorship.query.filter_by(mentor_id=current_user.id, status='accepted').all()
        pending_requests = Mentorship.query.filter_by(mentor_id=current_user.id, status='pending').count()
        return render_template('mentor_dashboard.html', 
                             mentees=mentees,
                             pending_requests=pending_requests)
    
    elif current_user.role == 'recruiter':
        jobs = Job.query.filter_by(recruiter_id=current_user.id).all()
        applications = sum(len(job.applications) for job in jobs)
        return render_template('recruiter_dashboard.html', 
                             jobs=jobs,
                             applications=applications)
    
    return redirect(url_for('main.index'))

@dashboard_bp.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=current_user)

@dashboard_bp.route('/skill-assessment')
@login_required
def skill_assessment():
    if current_user.role != 'women':
        flash('Access denied', 'error')
        return redirect(url_for('dashboard.index'))
    return render_template('skill_assessment.html')

@dashboard_bp.route('/progress-tracker')
@login_required
def progress_tracker():
    if current_user.role != 'women':
        flash('Access denied', 'error')
        return redirect(url_for('dashboard.index'))
    
    progress = Progress.query.filter_by(user_id=current_user.id).all()
    return render_template('progress_tracker.html', progress=progress)