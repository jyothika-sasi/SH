from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import Job, Application, User, db
from . import jobs_bp
from datetime import datetime

@jobs_bp.route('/jobs')
@login_required
def list_jobs():
    location = request.args.get('location', '')
    jobs = Job.query.filter_by(is_active=True)
    
    if location:
        jobs = jobs.filter(Job.location.contains(location))
    
    jobs = jobs.order_by(Job.posted_at.desc()).all()
    return render_template('jobs.html', jobs=jobs)

@jobs_bp.route('/job/<int:job_id>')
@login_required
def job_detail(job_id):
    job = Job.query.get_or_404(job_id)
    has_applied = False
    
    if current_user.role == 'women':
        has_applied = Application.query.filter_by(user_id=current_user.id, job_id=job_id).first() is not None
    
    return render_template('job_detail.html', job=job, has_applied=has_applied)

@jobs_bp.route('/apply-job/<int:job_id>', methods=['POST'])
@login_required
def apply_job(job_id):
    if current_user.role != 'women':
        flash('Only women can apply for jobs', 'error')
        return redirect(url_for('jobs.job_detail', job_id=job_id))
    
    job = Job.query.get_or_404(job_id)
    
    # Check if already applied
    existing = Application.query.filter_by(user_id=current_user.id, job_id=job_id).first()
    if existing:
        flash('You have already applied for this job', 'info')
        return redirect(url_for('jobs.job_detail', job_id=job_id))
    
    application = Application(
        user_id=current_user.id,
        job_id=job_id,
        resume=request.form.get('resume', ''),
        cover_letter=request.form.get('cover_letter', '')
    )
    
    db.session.add(application)
    db.session.commit()
    flash('Application submitted successfully!', 'success')
    return redirect(url_for('jobs.job_detail', job_id=job_id))

# Recruiter routes
@jobs_bp.route('/post-job', methods=['GET', 'POST'])
@login_required
def post_job():
    if current_user.role != 'recruiter':
        flash('Access denied', 'error')
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        job = Job(
            title=request.form.get('title'),
            description=request.form.get('description'),
            company=current_user.company,
            location=request.form.get('location'),
            requirements=request.form.get('requirements'),
            salary_range=request.form.get('salary_range'),
            recruiter_id=current_user.id
        )
        db.session.add(job)
        db.session.commit()
        flash('Job posted successfully!', 'success')
        return redirect(url_for('dashboard.index'))
    
    return render_template('post_job.html')

@jobs_bp.route('/my-job-listings')
@login_required
def my_job_listings():
    if current_user.role != 'recruiter':
        flash('Access denied', 'error')
        return redirect(url_for('dashboard.index'))
    
    jobs = Job.query.filter_by(recruiter_id=current_user.id).all()
    return render_template('my_job_listings.html', jobs=jobs)

@jobs_bp.route('/view-applicants/<int:job_id>')
@login_required
def view_applicants(job_id):
    if current_user.role != 'recruiter':
        flash('Access denied', 'error')
        return redirect(url_for('dashboard.index'))
    
    job = Job.query.get_or_404(job_id)
    if job.recruiter_id != current_user.id:
        flash('Access denied', 'error')
        return redirect(url_for('dashboard.index'))
    
    applications = Application.query.filter_by(job_id=job_id).all()
    return render_template('view_applicants.html', job=job, applications=applications)

@jobs_bp.route('/update-application/<int:app_id>/<string:status>')
@login_required
def update_application(app_id, status):
    if current_user.role != 'recruiter':
        flash('Access denied', 'error')
        return redirect(url_for('dashboard.index'))
    
    application = Application.query.get_or_404(app_id)
    job = Job.query.get(application.job_id)
    
    if job.recruiter_id != current_user.id:
        flash('Access denied', 'error')
        return redirect(url_for('dashboard.index'))
    
    application.status = status
    db.session.commit()
    flash(f'Application status updated to {status}', 'success')
    return redirect(url_for('jobs.view_applicants', job_id=job.id))