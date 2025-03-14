from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app import db
from app.models import User, Workout, WeightMachine, CardioType, WeightExercise, CardioExercise
from datetime import datetime, timedelta
import json
import pandas as pd
import plotly
import plotly.express as px
import plotly.graph_objects as go
import io
import base64
from sqlalchemy import func
import pytz
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify

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
    # Get the local timezone (America/Chicago for Central Time)
    local_tz = pytz.timezone('America/Chicago')
    
    # Get current time in UTC and convert to local time
    utc_now = datetime.utcnow()
    local_now = utc_now.replace(tzinfo=pytz.utc).astimezone(local_tz)
    
    # Remove timezone info for database storage
    local_now = local_now.replace(tzinfo=None)
    
    workout = Workout.query.get_or_404(workout_id)
    workout.start_time = local_now
    db.session.commit()
    
    # Format time in local timezone for display
    return jsonify({'success': True, 'time': local_now.strftime('%H:%M:%S')})

@main_bp.route('/workout/<int:workout_id>/stop', methods=['POST'])
def stop_workout(workout_id):
    # Get the local timezone (America/Chicago for Central Time)
    local_tz = pytz.timezone('America/Chicago')
    
    # Get current time in UTC and convert to local time
    utc_now = datetime.utcnow()
    local_now = utc_now.replace(tzinfo=pytz.utc).astimezone(local_tz)
    
    # Remove timezone info for database storage
    local_now = local_now.replace(tzinfo=None)
    
    workout = Workout.query.get_or_404(workout_id)
    workout.end_time = local_now
    db.session.commit()
    
    # Format time in local timezone for display
    return jsonify({'success': True, 'time': local_now.strftime('%H:%M:%S')})

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
        print(f"DEBUG - Generating weight graph for user {user_id}, machine {selected_machine_id}")
        weight_graph = generate_weight_graph(user_id, selected_machine_id, start_date, end_date)
        print(f"DEBUG - Weight graph type: {type(weight_graph)}")
        print(f"DEBUG - Weight graph content (first 100 chars): {weight_graph[:100] if weight_graph else 'None'}")
        
        reps_graph = generate_reps_graph(user_id, selected_machine_id, start_date, end_date)
        print(f"DEBUG - Reps graph type: {type(reps_graph)}")
        print(f"DEBUG - Reps graph content (first 100 chars): {reps_graph[:100] if reps_graph else 'None'}")
    
    # Cardio stats if cardio type selected
    if selected_cardio_id:
        cardio_duration_graph = generate_cardio_duration_graph(user_id, selected_cardio_id, start_date, end_date)
        cardio_distance_graph = generate_cardio_distance_graph(user_id, selected_cardio_id, start_date, end_date)
        
    # Create default empty graphs if none were generated
    if weight_graph is None:
        weight_graph = create_empty_graph('No Weight Data Available')
        
    if reps_graph is None:
        reps_graph = create_empty_graph('No Repetition Data Available')
        
    if cardio_duration_graph is None:
        cardio_duration_graph = create_empty_graph('No Duration Data Available')
        
    if cardio_distance_graph is None:
        cardio_distance_graph = create_empty_graph('No Distance Data Available')
    
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
    
    # Get machine name for the title
    machine_name = WeightMachine.query.get(machine_id).name
    
    # Prepare data for plotting
    data = []
    for ex in exercises:
        # Parse sets_reps_weight to extract information for hover
        sets_info = []
        sets = ex.sets_reps_weight.split(',')
        for set_info in sets:
            set_info = set_info.strip()
            if 'x' in set_info and 'at' in set_info:
                try:
                    sets_reps, weight_part = set_info.split('at')
                    sets_reps = sets_reps.strip()
                    weight = weight_part.strip()
                    sets_info.append(f"{sets_reps} at {weight}")
                except (ValueError, IndexError):
                    pass
        
        data.append({
            'date': ex.workout.date.strftime('%Y-%m-%d'),
            'weight': ex.average_weight,
            'sets_info': '<br>'.join(sets_info),
            'total_reps': ex.total_reps
        })
    
    # Create interactive plot with Plotly
    df = pd.DataFrame(data)
    
    # Check if we have data
    if df.empty:
        # Create an empty figure with a message
        fig = go.Figure()
        fig.add_annotation(text="No data available for the selected period",
                          xref="paper", yref="paper",
                          x=0.5, y=0.5, showarrow=False)
    else:
        # Create the line plot
        fig = px.line(df, x='date', y='weight', markers=True, title=f'Average Weight Over Time - {machine_name}')
    
    # Add hover data if we have data
    if not df.empty:
        hover_data = []
        for i, row in df.iterrows():
            hover_data.append(
                f"<b>Date:</b> {row['date']}<br>"
                f"<b>Weight:</b> {row['weight']:.1f} lbs<br>"
                f"<b>Sets & Reps:</b><br>{row['sets_info']}<br>"
                f"<b>Total Reps:</b> {row['total_reps']}"
            )
        
        fig.update_traces(
            hovertemplate='%{customdata}<extra></extra>',
            customdata=hover_data
        )
    
    # Customize layout
    fig.update_layout(
        xaxis_title='Date',
        yaxis_title='Average Weight (lbs)',
        hovermode='closest',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Arial, sans-serif')
    )
    
    # Convert to JSON for the template
    graph_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    print(f"DEBUG - Generated graph JSON length: {len(graph_json)}")
    return graph_json

def create_empty_graph(title_text):
    """Create an empty graph with a message when no data is available"""
    fig = {
        'data': [],
        'layout': {
            'title': title_text,
            'annotations': [{
                'text': 'No data available for the selected period',
                'showarrow': False,
                'font': {'size': 16},
                'xref': 'paper',
                'yref': 'paper',
                'x': 0.5,
                'y': 0.5
            }]
        }
    }
    json_data = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    print(f"DEBUG - Empty graph JSON: {json_data[:100]}...")
    return json_data

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
    
    # Get machine name for the title
    machine_name = WeightMachine.query.get(machine_id).name
    
    # Prepare data for plotting
    data = []
    for ex in exercises:
        # Parse sets_reps_weight to extract information for hover
        sets_info = []
        sets = ex.sets_reps_weight.split(',')
        for set_info in sets:
            set_info = set_info.strip()
            if 'x' in set_info and 'at' in set_info:
                try:
                    sets_reps, weight_part = set_info.split('at')
                    sets_reps = sets_reps.strip()
                    weight = weight_part.strip()
                    sets_info.append(f"{sets_reps} at {weight}")
                except (ValueError, IndexError):
                    pass
        
        data.append({
            'date': ex.workout.date.strftime('%Y-%m-%d'),
            'total_reps': ex.total_reps,
            'sets_info': '<br>'.join(sets_info),
            'weight': ex.average_weight
        })
    
    # Create interactive plot with Plotly
    df = pd.DataFrame(data)
    
    # Check if we have data
    if df.empty:
        # Create an empty figure with a message
        fig = go.Figure()
        fig.add_annotation(text="No data available for the selected period",
                          xref="paper", yref="paper",
                          x=0.5, y=0.5, showarrow=False)
    else:
        # Create the line plot
        fig = px.line(df, x='date', y='total_reps', markers=True, title=f'Total Repetitions Over Time - {machine_name}')
    
    # Add hover data if we have data
    if not df.empty:
        hover_data = []
        for i, row in df.iterrows():
            hover_data.append(
                f"<b>Date:</b> {row['date']}<br>"
                f"<b>Total Reps:</b> {row['total_reps']}<br>"
                f"<b>Sets & Reps:</b><br>{row['sets_info']}<br>"
                f"<b>Average Weight:</b> {row['weight']:.1f} lbs"
            )
        
        fig.update_traces(
            hovertemplate='%{customdata}<extra></extra>',
            customdata=hover_data
        )
    
    # Customize layout
    fig.update_layout(
        xaxis_title='Date',
        yaxis_title='Total Repetitions',
        hovermode='closest',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Arial, sans-serif')
    )
    
    # Convert to JSON for the template
    graph_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    print(f"DEBUG - Generated reps graph JSON length: {len(graph_json)}")
    print(f"DEBUG - First 200 chars of reps graph JSON: {graph_json[:200]}")
    return graph_json

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
    
    # Get cardio type name for the title
    cardio_name = CardioType.query.get(cardio_type_id).name
    
    # Prepare data for plotting
    data = []
    for ex in exercises:
        if ex.duration:  # Only include exercises with duration
            # Format duration for display
            duration_display = ex.duration if ex.duration else 'N/A'
            distance_display = f"{ex.distance:.2f} miles" if ex.distance else 'N/A'
            calories_display = f"{ex.calories} cal" if ex.calories else 'N/A'
            
            data.append({
                'date': ex.workout.date.strftime('%Y-%m-%d'),
                'duration': ex.duration_minutes,
                'duration_display': duration_display,
                'distance_display': distance_display,
                'calories_display': calories_display
            })
    
    # Create interactive plot with Plotly
    df = pd.DataFrame(data)
    
    # Check if we have data
    if df.empty:
        # Create an empty figure with a message
        fig = go.Figure()
        fig.add_annotation(text="No data available for the selected period",
                          xref="paper", yref="paper",
                          x=0.5, y=0.5, showarrow=False)
    else:
        # Create the line plot
        fig = px.line(df, x='date', y='duration', markers=True, title=f'Cardio Duration Over Time - {cardio_name}')
    
    # Add hover data if we have data
    if not df.empty:
        hover_data = []
        for i, row in df.iterrows():
            hover_data.append(
                f"<b>Date:</b> {row['date']}<br>"
                f"<b>Duration:</b> {row['duration_display']}<br>"
                f"<b>Distance:</b> {row['distance_display']}<br>"
                f"<b>Calories:</b> {row['calories_display']}"
            )
        
        fig.update_traces(
            hovertemplate='%{customdata}<extra></extra>',
            customdata=hover_data
        )
    
    # Customize layout
    fig.update_layout(
        xaxis_title='Date',
        yaxis_title='Duration (minutes)',
        hovermode='closest',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Arial, sans-serif')
    )
    
    # Convert to JSON for the template
    graph_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    print(f"DEBUG - Generated reps graph JSON length: {len(graph_json)}")
    print(f"DEBUG - First 200 chars of reps graph JSON: {graph_json[:200]}")
    return graph_json

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
    
    # Get cardio type name for the title
    cardio_name = CardioType.query.get(cardio_type_id).name
    
    # Prepare data for plotting
    data = []
    for ex in exercises:
        if ex.distance:  # Only include exercises with distance
            # Format data for display
            duration_display = ex.duration if ex.duration else 'N/A'
            calories_display = f"{ex.calories} cal" if ex.calories else 'N/A'
            
            # Calculate pace (minutes per mile) if both duration and distance are available
            pace_display = 'N/A'
            if ex.duration_minutes and ex.distance and ex.distance > 0:
                pace = ex.duration_minutes / ex.distance
                minutes = int(pace)
                seconds = int((pace - minutes) * 60)
                pace_display = f"{minutes}:{seconds:02d} min/mile"
            
            data.append({
                'date': ex.workout.date.strftime('%Y-%m-%d'),
                'distance': ex.distance,
                'duration_display': duration_display,
                'pace_display': pace_display,
                'calories_display': calories_display
            })
    
    # Create interactive plot with Plotly
    df = pd.DataFrame(data)
    
    # Check if we have data
    if df.empty:
        # Create an empty figure with a message
        fig = go.Figure()
        fig.add_annotation(text="No data available for the selected period",
                          xref="paper", yref="paper",
                          x=0.5, y=0.5, showarrow=False)
    else:
        # Create the line plot
        fig = px.line(df, x='date', y='distance', markers=True, title=f'Cardio Distance Over Time - {cardio_name}')
    
    # Add hover data if we have data
    if not df.empty:
        hover_data = []
        for i, row in df.iterrows():
            hover_data.append(
                f"<b>Date:</b> {row['date']}<br>"
                f"<b>Distance:</b> {row['distance']:.2f} miles<br>"
                f"<b>Duration:</b> {row['duration_display']}<br>"
                f"<b>Pace:</b> {row['pace_display']}<br>"
                f"<b>Calories:</b> {row['calories_display']}"
            )
        
        fig.update_traces(
            hovertemplate='%{customdata}<extra></extra>',
            customdata=hover_data
        )
    
    # Customize layout
    fig.update_layout(
        xaxis_title='Date',
        yaxis_title='Distance (miles)',
        hovermode='closest',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Arial, sans-serif')
    )
    
    # Convert to JSON for the template
    graph_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    print(f"DEBUG - Generated reps graph JSON length: {len(graph_json)}")
    print(f"DEBUG - First 200 chars of reps graph JSON: {graph_json[:200]}")
    return graph_json
