from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import Mentorship, User, db
from . import mentor_bp
from datetime import datetime

@mentor_bp.route('/mentors')
@login_required
def list_mentors():
    expertise = request.args.get('expertise', '')
    mentors = User.query.filter_by(role='mentor')
    
    if expertise:
        mentors = mentors.filter(User.expertise.contains(expertise))
    
    mentors = mentors.all()
    return render_template('mentors.html', mentors=mentors)

@mentor_bp.route('/mentor/<int:mentor_id>')
@login_required
def mentor_detail(mentor_id):
    mentor = User.query.get_or_404(mentor_id)
    if mentor.role != 'mentor':
        flash('User is not a mentor', 'error')
        return redirect(url_for('mentor.list_mentors'))
    
    has_requested = False
    if current_user.role == 'women':
        has_requested = Mentorship.query.filter_by(
            mentee_id=current_user.id, 
            mentor_id=mentor_id
        ).first() is not None
    
    return render_template('mentor_detail.html', mentor=mentor, has_requested=has_requested)

@mentor_bp.route('/request-mentor/<int:mentor_id>', methods=['POST'])
@login_required
def request_mentor(mentor_id):
    if current_user.role != 'women':
        flash('Only women can request mentorship', 'error')
        return redirect(url_for('mentor.mentor_detail', mentor_id=mentor_id))
    
    mentor = User.query.get_or_404(mentor_id)
    if mentor.role != 'mentor':
        flash('User is not a mentor', 'error')
        return redirect(url_for('mentor.list_mentors'))
    
    # Check if already requested
    existing = Mentorship.query.filter_by(
        mentee_id=current_user.id, 
        mentor_id=mentor_id
    ).first()
    
    if existing:
        flash('You have already sent a request to this mentor', 'info')
        return redirect(url_for('mentor.mentor_detail', mentor_id=mentor_id))
    
    mentorship = Mentorship(
        mentee_id=current_user.id,
        mentor_id=mentor_id,
        status='pending',
        session_notes=request.form.get('message', '')
    )
    
    db.session.add(mentorship)
    db.session.commit()
    flash('Mentorship request sent successfully!', 'success')
    return redirect(url_for('mentor.mentor_detail', mentor_id=mentor_id))

# Mentor specific routes
@mentor_bp.route('/mentorship-requests')
@login_required
def mentorship_requests():
    if current_user.role != 'mentor':
        flash('Access denied', 'error')
        return redirect(url_for('dashboard.index'))
    
    requests = Mentorship.query.filter_by(
        mentor_id=current_user.id, 
        status='pending'
    ).all()
    
    return render_template('mentorship_requests.html', requests=requests)

@mentor_bp.route('/accept-mentor/<int:request_id>')
@login_required
def accept_mentor(request_id):
    mentorship = Mentorship.query.get_or_404(request_id)
    
    if mentorship.mentor_id != current_user.id:
        flash('Access denied', 'error')
        return redirect(url_for('dashboard.index'))
    
    mentorship.status = 'accepted'
    db.session.commit()
    flash('Mentorship request accepted!', 'success')
    return redirect(url_for('mentor.mentorship_requests'))

@mentor_bp.route('/reject-mentor/<int:request_id>')
@login_required
def reject_mentor(request_id):
    mentorship = Mentorship.query.get_or_404(request_id)
    
    if mentorship.mentor_id != current_user.id:
        flash('Access denied', 'error')
        return redirect(url_for('dashboard.index'))
    
    mentorship.status = 'rejected'
    db.session.commit()
    flash('Mentorship request rejected', 'info')
    return redirect(url_for('mentor.mentorship_requests'))

@mentor_bp.route('/my-mentees')
@login_required
def my_mentees():
    if current_user.role != 'mentor':
        flash('Access denied', 'error')
        return redirect(url_for('dashboard.index'))
    
    mentees = Mentorship.query.filter_by(
        mentor_id=current_user.id, 
        status='accepted'
    ).all()
    
    return render_template('my_mentees.html', mentees=mentees)

@mentor_bp.route('/schedule-session/<int:mentorship_id>', methods=['POST'])
@login_required
def schedule_session(mentorship_id):
    if current_user.role != 'mentor':
        flash('Access denied', 'error')
        return redirect(url_for('dashboard.index'))
    
    mentorship = Mentorship.query.get_or_404(mentorship_id)
    
    if mentorship.mentor_id != current_user.id:
        flash('Access denied', 'error')
        return redirect(url_for('dashboard.index'))
    
    # Parse datetime from form
    session_date = datetime.strptime(
        request.form.get('session_date'), 
        '%Y-%m-%dT%H:%M'
    )
    
    mentorship.scheduled_date = session_date
    db.session.commit()
    flash('Session scheduled successfully!', 'success')
    return redirect(url_for('mentor.my_mentees'))