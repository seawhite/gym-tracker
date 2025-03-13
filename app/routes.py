from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app import db
from app.models import User, Workout, WeightMachine, CardioType, WeightExercise, CardioExercise
from datetime import datetime, timedelta
import json
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import io
import base64
from sqlalchemy import func

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    users = User.query.order_by(User.name).all()
    return render_template('index.html', users=users)

@main_bp.route('/add_user', methods=['POST'])
def add_user():
    name = request.form.get('name')
    if name:
        # Check if user already exists
        existing_user = User.query.filter_by(name=name).first()
        if existing_user:
            flash(f'User {name} already exists!', 'warning')
        else:
            new_user = User(name=name)
            db.session.add(new_user)
            db.session.commit()
            flash(f'User {name} added successfully!', 'success')
    return redirect(url_for('main.index'))

@main_bp.route('/user/<int:user_id>')
def user_profile(user_id):
    user = User.query.get_or_404(user_id)
    workouts = Workout.query.filter_by(user_id=user_id).order_by(Workout.date.desc()).all()
    return render_template('user_profile.html', user=user, workouts=workouts)

@main_bp.route('/user/<int:user_id>/new_workout')
def new_workout(user_id):
    user = User.query.get_or_404(user_id)
    
    # Get all weight machines and cardio types for dropdowns
    weight_machines = WeightMachine.query.order_by(WeightMachine.name).all()
    cardio_types = CardioType.query.order_by(CardioType.name).all()
    
    # Create a new workout
    workout = Workout(user_id=user_id, date=datetime.utcnow().date())
    db.session.add(workout)
    db.session.commit()
    
    return render_template('workout.html', 
                          user=user, 
                          workout=workout, 
                          weight_machines=weight_machines, 
                          cardio_types=cardio_types)

@main_bp.route('/workout/<int:workout_id>/start', methods=['POST'])
def start_workout(workout_id):
    workout = Workout.query.get_or_404(workout_id)
    workout.start_time = datetime.utcnow()
    db.session.commit()
    return jsonify({'success': True, 'time': workout.start_time.strftime('%H:%M:%S')})

@main_bp.route('/workout/<int:workout_id>/stop', methods=['POST'])
def stop_workout(workout_id):
    workout = Workout.query.get_or_404(workout_id)
    workout.end_time = datetime.utcnow()
    db.session.commit()
    return jsonify({'success': True, 'time': workout.end_time.strftime('%H:%M:%S')})

@main_bp.route('/add_weight_machine', methods=['POST'])
def add_weight_machine():
    name = request.form.get('name')
    if name:
        existing = WeightMachine.query.filter_by(name=name).first()
        if not existing:
            machine = WeightMachine(name=name)
            db.session.add(machine)
            db.session.commit()
            return jsonify({'success': True, 'id': machine.id, 'name': machine.name})
        return jsonify({'success': False, 'message': 'Machine already exists'})
    return jsonify({'success': False, 'message': 'Name is required'})

@main_bp.route('/add_cardio_type', methods=['POST'])
def add_cardio_type():
    name = request.form.get('name')
    if name:
        existing = CardioType.query.filter_by(name=name).first()
        if not existing:
            cardio_type = CardioType(name=name)
            db.session.add(cardio_type)
            db.session.commit()
            return jsonify({'success': True, 'id': cardio_type.id, 'name': cardio_type.name})
        return jsonify({'success': False, 'message': 'Cardio type already exists'})
    return jsonify({'success': False, 'message': 'Name is required'})

@main_bp.route('/workout/<int:workout_id>/add_weight_exercise', methods=['POST'])
def add_weight_exercise(workout_id):
    workout = Workout.query.get_or_404(workout_id)
    
    machine_id = request.form.get('machine_id')
    sets_reps_weight = request.form.get('sets_reps_weight')
    seat_height = request.form.get('seat_height')
    other_parameters = request.form.get('other_parameters')
    confidence = request.form.get('confidence', 'medium')
    
    if machine_id and sets_reps_weight:
        exercise = WeightExercise(
            workout_id=workout_id,
            machine_id=machine_id,
            sets_reps_weight=sets_reps_weight,
            seat_height=seat_height,
            other_parameters=other_parameters,
            confidence=confidence
        )
        db.session.add(exercise)
        db.session.commit()
        
        machine = WeightMachine.query.get(machine_id)
        return jsonify({
            'success': True, 
            'id': exercise.id,
            'machine_name': machine.name,
            'sets_reps_weight': sets_reps_weight,
            'seat_height': seat_height,
            'other_parameters': other_parameters,
            'confidence': confidence
        })
    
    return jsonify({'success': False, 'message': 'Machine and sets/reps/weight are required'})

@main_bp.route('/workout/<int:workout_id>/add_cardio_exercise', methods=['POST'])
def add_cardio_exercise(workout_id):
    workout = Workout.query.get_or_404(workout_id)
    
    cardio_type_id = request.form.get('cardio_type_id')
    duration = request.form.get('duration')
    distance = request.form.get('distance')
    calories = request.form.get('calories')
    incline = request.form.get('incline')
    resistance = request.form.get('resistance')
    
    if cardio_type_id:
        exercise = CardioExercise(
            workout_id=workout_id,
            cardio_type_id=cardio_type_id,
            duration=duration,
            distance=float(distance) if distance else None,
            calories=int(calories) if calories else None,
            incline=float(incline) if incline else None,
            resistance=float(resistance) if resistance else None
        )
        db.session.add(exercise)
        db.session.commit()
        
        cardio_type = CardioType.query.get(cardio_type_id)
        return jsonify({
            'success': True, 
            'id': exercise.id,
            'cardio_type_name': cardio_type.name,
            'duration': duration,
            'distance': distance,
            'calories': calories,
            'incline': incline,
            'resistance': resistance
        })
    
    return jsonify({'success': False, 'message': 'Cardio type is required'})

@main_bp.route('/workout/<int:workout_id>/complete', methods=['POST'])
def complete_workout(workout_id):
    workout = Workout.query.get_or_404(workout_id)
    
    # If end time not set, set it now
    if not workout.end_time and workout.start_time:
        workout.end_time = datetime.utcnow()
        
    db.session.commit()
    return redirect(url_for('main.user_profile', user_id=workout.user_id))

@main_bp.route('/workout/<int:workout_id>')
def view_workout(workout_id):
    workout = Workout.query.get_or_404(workout_id)
    return render_template('view_workout.html', workout=workout)

@main_bp.route('/workout/<int:workout_id>/edit')
def edit_workout(workout_id):
    workout = Workout.query.get_or_404(workout_id)
    weight_machines = WeightMachine.query.order_by(WeightMachine.name).all()
    cardio_types = CardioType.query.order_by(CardioType.name).all()
    
    return render_template('edit_workout.html', 
                          workout=workout, 
                          weight_machines=weight_machines, 
                          cardio_types=cardio_types)

@main_bp.route('/workout/<int:workout_id>/delete', methods=['POST'])
def delete_workout(workout_id):
    workout = Workout.query.get_or_404(workout_id)
    user_id = workout.user_id
    
    # Delete all weight exercises associated with this workout
    WeightExercise.query.filter_by(workout_id=workout_id).delete()
    
    # Delete all cardio exercises associated with this workout
    CardioExercise.query.filter_by(workout_id=workout_id).delete()
    
    # Delete the workout itself
    db.session.delete(workout)
    db.session.commit()
    
    flash('Workout deleted successfully!', 'success')
    return redirect(url_for('main.user_profile', user_id=user_id))

@main_bp.route('/exercise/weight/<int:exercise_id>/delete', methods=['POST'])
def delete_weight_exercise(exercise_id):
    exercise = WeightExercise.query.get_or_404(exercise_id)
    workout_id = exercise.workout_id
    
    db.session.delete(exercise)
    db.session.commit()
    
    return jsonify({'success': True})

@main_bp.route('/exercise/cardio/<int:exercise_id>/delete', methods=['POST'])
def delete_cardio_exercise(exercise_id):
    exercise = CardioExercise.query.get_or_404(exercise_id)
    workout_id = exercise.workout_id
    
    db.session.delete(exercise)
    db.session.commit()
    
    return jsonify({'success': True})

@main_bp.route('/exercise/weight/<int:exercise_id>/update', methods=['POST'])
def update_weight_exercise(exercise_id):
    exercise = WeightExercise.query.get_or_404(exercise_id)
    
    exercise.machine_id = request.form.get('machine_id', exercise.machine_id)
    exercise.sets_reps_weight = request.form.get('sets_reps_weight', exercise.sets_reps_weight)
    exercise.seat_height = request.form.get('seat_height', exercise.seat_height)
    exercise.other_parameters = request.form.get('other_parameters', exercise.other_parameters)
    exercise.confidence = request.form.get('confidence', exercise.confidence)
    
    db.session.commit()
    return jsonify({'success': True})

@main_bp.route('/exercise/cardio/<int:exercise_id>/update', methods=['POST'])
def update_cardio_exercise(exercise_id):
    exercise = CardioExercise.query.get_or_404(exercise_id)
    
    exercise.cardio_type_id = request.form.get('cardio_type_id', exercise.cardio_type_id)
    exercise.duration = request.form.get('duration', exercise.duration)
    
    if request.form.get('distance'):
        exercise.distance = float(request.form.get('distance'))
    if request.form.get('calories'):
        exercise.calories = int(request.form.get('calories'))
    if request.form.get('incline'):
        exercise.incline = float(request.form.get('incline'))
    if request.form.get('resistance'):
        exercise.resistance = float(request.form.get('resistance'))
    
    db.session.commit()
    return jsonify({'success': True})

@main_bp.route('/user/<int:user_id>/stats')
def user_stats(user_id):
    user = User.query.get_or_404(user_id)
    
    # Get date range parameters
    days = request.args.get('days', '30')
    try:
        days = int(days)
    except ValueError:
        days = 30
    
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=days)
    
    # Get all weight machines and cardio types for filtering
    weight_machines = WeightMachine.query.order_by(WeightMachine.name).all()
    cardio_types = CardioType.query.order_by(CardioType.name).all()
    
    # Selected machine/cardio type for detailed view
    selected_machine_id = request.args.get('machine_id')
    selected_cardio_id = request.args.get('cardio_id')
    
    # Generate graphs
    weight_graph = None
    reps_graph = None
    cardio_duration_graph = None
    cardio_distance_graph = None
    
    # Weight lifting stats if machine selected
    if selected_machine_id:
        weight_graph = generate_weight_graph(user_id, selected_machine_id, start_date, end_date)
        reps_graph = generate_reps_graph(user_id, selected_machine_id, start_date, end_date)
    
    # Cardio stats if cardio type selected
    if selected_cardio_id:
        cardio_duration_graph = generate_cardio_duration_graph(user_id, selected_cardio_id, start_date, end_date)
        cardio_distance_graph = generate_cardio_distance_graph(user_id, selected_cardio_id, start_date, end_date)
    
    return render_template('user_stats.html',
                          user=user,
                          days=days,
                          weight_machines=weight_machines,
                          cardio_types=cardio_types,
                          selected_machine_id=selected_machine_id,
                          selected_cardio_id=selected_cardio_id,
                          weight_graph=weight_graph,
                          reps_graph=reps_graph,
                          cardio_duration_graph=cardio_duration_graph,
                          cardio_distance_graph=cardio_distance_graph)

def generate_weight_graph(user_id, machine_id, start_date, end_date):
    # Query weight exercises for the specified machine
    exercises = WeightExercise.query.join(Workout).filter(
        Workout.user_id == user_id,
        WeightExercise.machine_id == machine_id,
        Workout.date >= start_date,
        Workout.date <= end_date
    ).order_by(Workout.date).all()
    
    if not exercises:
        return None
    
    # Prepare data for plotting
    dates = [ex.workout.date for ex in exercises]
    avg_weights = [ex.average_weight for ex in exercises]
    
    # Create the plot
    plt.figure(figsize=(10, 6))
    plt.plot(dates, avg_weights, marker='o', linestyle='-')
    plt.title('Average Weight Over Time')
    plt.xlabel('Date')
    plt.ylabel('Average Weight (lbs)')
    plt.grid(True)
    plt.tight_layout()
    
    # Convert plot to base64 string
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plt.close()
    
    return base64.b64encode(img.getvalue()).decode()

def generate_reps_graph(user_id, machine_id, start_date, end_date):
    # Query weight exercises for the specified machine
    exercises = WeightExercise.query.join(Workout).filter(
        Workout.user_id == user_id,
        WeightExercise.machine_id == machine_id,
        Workout.date >= start_date,
        Workout.date <= end_date
    ).order_by(Workout.date).all()
    
    if not exercises:
        return None
    
    # Prepare data for plotting
    dates = [ex.workout.date for ex in exercises]
    total_reps = [ex.total_reps for ex in exercises]
    
    # Create the plot
    plt.figure(figsize=(10, 6))
    plt.plot(dates, total_reps, marker='o', linestyle='-')
    plt.title('Total Repetitions Over Time')
    plt.xlabel('Date')
    plt.ylabel('Total Repetitions')
    plt.grid(True)
    plt.tight_layout()
    
    # Convert plot to base64 string
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plt.close()
    
    return base64.b64encode(img.getvalue()).decode()

def generate_cardio_duration_graph(user_id, cardio_type_id, start_date, end_date):
    # Query cardio exercises for the specified type
    exercises = CardioExercise.query.join(Workout).filter(
        Workout.user_id == user_id,
        CardioExercise.cardio_type_id == cardio_type_id,
        Workout.date >= start_date,
        Workout.date <= end_date
    ).order_by(Workout.date).all()
    
    if not exercises:
        return None
    
    # Prepare data for plotting
    dates = [ex.workout.date for ex in exercises]
    durations = [ex.duration_minutes for ex in exercises]
    
    # Create the plot
    plt.figure(figsize=(10, 6))
    plt.plot(dates, durations, marker='o', linestyle='-')
    plt.title('Cardio Duration Over Time')
    plt.xlabel('Date')
    plt.ylabel('Duration (minutes)')
    plt.grid(True)
    plt.tight_layout()
    
    # Convert plot to base64 string
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plt.close()
    
    return base64.b64encode(img.getvalue()).decode()

def generate_cardio_distance_graph(user_id, cardio_type_id, start_date, end_date):
    # Query cardio exercises for the specified type
    exercises = CardioExercise.query.join(Workout).filter(
        Workout.user_id == user_id,
        CardioExercise.cardio_type_id == cardio_type_id,
        Workout.date >= start_date,
        Workout.date <= end_date,
        CardioExercise.distance.isnot(None)  # Only include exercises with distance data
    ).order_by(Workout.date).all()
    
    if not exercises:
        return None
    
    # Prepare data for plotting
    dates = [ex.workout.date for ex in exercises]
    distances = [ex.distance for ex in exercises]
    
    # Create the plot
    plt.figure(figsize=(10, 6))
    plt.plot(dates, distances, marker='o', linestyle='-')
    plt.title('Cardio Distance Over Time')
    plt.xlabel('Date')
    plt.ylabel('Distance (miles)')
    plt.grid(True)
    plt.tight_layout()
    
    # Convert plot to base64 string
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plt.close()
    
    return base64.b64encode(img.getvalue()).decode()
