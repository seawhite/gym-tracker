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
        weight_graph = generate_weight_graph(user_id, selected_machine_id, start_date, end_date)
        
        reps_graph = generate_reps_graph(user_id, selected_machine_id, start_date, end_date)
    
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
        
        # Use end_time if available, otherwise fallback to date with 00:00 time
        timestamp = ex.workout.end_time if ex.workout.end_time else datetime.combine(ex.workout.date, datetime.min.time())
        
        # Ensure weight and total_reps are numeric values
        avg_weight = float(ex.average_weight) if ex.average_weight is not None else 0
        total_reps = float(ex.total_reps) if ex.total_reps is not None else 0
        
        data.append({
            'date': timestamp.strftime('%Y-%m-%d %H:%M'),
            'timestamp': timestamp,
            'weight': avg_weight,  # Use the explicitly converted numeric value
            'sets_info': '<br>'.join(sets_info),
            'total_reps': total_reps  # Use the explicitly converted numeric value
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
        # Create a completely new approach for plotting
        # Convert data to simple lists of numbers for x and y
        x_values = list(range(len(df)))
        y_values = [float(val) for val in df['weight'].values]
        
        # Debug: print the actual values being used for the graph
        print("DEBUG: Data values for weight graph:")
        for i, (x, y, ts) in enumerate(zip(x_values, y_values, df['timestamp'])):
            print(f"DEBUG: {i}: x={x}, y={y} lbs, ts={ts}")
        
        # Create the plot with numeric indices for x-axis
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=x_values,
            y=y_values,
            mode='lines+markers',
            name='Average Weight'
        ))
        
        # Add custom x-axis labels with the timestamps
        fig.update_layout(
            xaxis=dict(
                tickmode='array',
                tickvals=x_values,
                ticktext=[ts.strftime('%Y-%m-%d %H:%M') for ts in df['timestamp']]
            )
        )
        fig.update_layout(title=f'Average Weight Over Time - {machine_name}')
        
        # Format the x-axis to show date and time
        fig.update_xaxes(tickformat='%Y-%m-%d %H:%M')
    
    # Add hover data if we have data
    if not df.empty:
        hover_data = []
        for i, row in df.iterrows():
            hover_data.append(
                f"<b>Date & Time:</b> {row['date']}<br>"
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
    
    # Set Y-axis to start at 0 and have appropriate range based on data
    if not df.empty:
        max_weight = df['weight'].max()
        # Add 10% padding to the top of the range
        y_max = max_weight * 1.1
        fig.update_yaxes(range=[0, y_max], dtick=max(5, int(max_weight/5)))
    
    # Convert to JSON for the template
    graph_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
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
        
        # Use end_time if available, otherwise fallback to date with 00:00 time
        timestamp = ex.workout.end_time if ex.workout.end_time else datetime.combine(ex.workout.date, datetime.min.time())
        
        # Debug: print the total_reps value
        print(f"DEBUG: Exercise {ex.id} has {ex.total_reps} total reps, sets_reps_weight: {ex.sets_reps_weight}")
        
        # Ensure total_reps is a numeric value
        total_reps = float(ex.total_reps) if ex.total_reps is not None else 0
        avg_weight = float(ex.average_weight) if ex.average_weight is not None else 0
        
        data.append({
            'date': timestamp.strftime('%Y-%m-%d %H:%M'),
            'timestamp': timestamp,
            'total_reps': total_reps,  # Use the explicitly converted numeric value
            'sets_info': '<br>'.join(sets_info),
            'weight': avg_weight  # Use the explicitly converted numeric value
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
        # Create a completely new approach for plotting
        # Convert data to simple lists of numbers for x and y
        x_values = list(range(len(df)))
        y_values = [float(val) for val in df['total_reps'].values]
        
        # Debug: print the actual values being used for the graph
        print("DEBUG: Data values for reps graph:")
        for i, (x, y, ts) in enumerate(zip(x_values, y_values, df['timestamp'])):
            print(f"DEBUG: {i}: x={x}, y={y} reps, ts={ts}")
        
        # Create the plot with numeric indices for x-axis
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=x_values,
            y=y_values,
            mode='lines+markers',
            name='Total Reps'
        ))
        
        # Add custom x-axis labels with the timestamps
        fig.update_layout(
            xaxis=dict(
                tickmode='array',
                tickvals=x_values,
                ticktext=[ts.strftime('%Y-%m-%d %H:%M') for ts in df['timestamp']]
            )
        )
        fig.update_layout(title=f'Total Repetitions Over Time - {machine_name}')
        
        # Format the x-axis to show date and time
        fig.update_xaxes(tickformat='%Y-%m-%d %H:%M')
    
    # Add hover data if we have data
    if not df.empty:
        hover_data = []
        for i, row in df.iterrows():
            hover_data.append(
                f"<b>Date & Time:</b> {row['date']}<br>"
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
    
    # Set Y-axis to start at 0 and have appropriate range based on data
    if not df.empty:
        max_reps = df['total_reps'].max()
        # Add 10% padding to the top of the range
        y_max = max_reps * 1.1
        fig.update_yaxes(range=[0, y_max], dtick=max(1, int(max_reps/5)))
    
    # Convert to JSON for the template
    graph_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
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
            
            # Use end_time if available, otherwise fallback to date with 00:00 time
            timestamp = ex.workout.end_time if ex.workout.end_time else datetime.combine(ex.workout.date, datetime.min.time())
            
            # Ensure duration is a numeric value
            duration_minutes = float(ex.duration_minutes) if ex.duration_minutes is not None else 0
            
            data.append({
                'date': timestamp.strftime('%Y-%m-%d %H:%M'),
                'timestamp': timestamp,
                'duration': duration_minutes,  # Use the explicitly converted numeric value
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
        # Create a completely new approach for plotting
        # Convert data to simple lists of numbers for x and y
        x_values = list(range(len(df)))
        y_values = [float(val) for val in df['duration'].values]
        
        # Debug: print the actual values being used for the graph
        print("DEBUG: Data values for cardio duration graph:")
        for i, (x, y, ts) in enumerate(zip(x_values, y_values, df['timestamp'])):
            print(f"DEBUG: {i}: x={x}, y={y} minutes, ts={ts}")
        
        # Create the plot with numeric indices for x-axis
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=x_values,
            y=y_values,
            mode='lines+markers',
            name='Duration'
        ))
        
        # Add custom x-axis labels with the timestamps
        fig.update_layout(
            xaxis=dict(
                tickmode='array',
                tickvals=x_values,
                ticktext=[ts.strftime('%Y-%m-%d %H:%M') for ts in df['timestamp']]
            )
        )
        fig.update_layout(title=f'Cardio Duration Over Time - {cardio_name}')
        
        # Format the x-axis to show date and time
        fig.update_xaxes(tickformat='%Y-%m-%d %H:%M')
    
    # Add hover data if we have data
    if not df.empty:
        hover_data = []
        for i, row in df.iterrows():
            hover_data.append(
                f"<b>Date & Time:</b> {row['date']}<br>"
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
    
    # Set Y-axis to start at 0 and have appropriate range based on data
    if not df.empty:
        max_duration = max(y_values)  # Use the y_values list we created earlier
        # Add 10% padding to the top of the range
        y_max = max_duration * 1.1
        fig.update_yaxes(range=[0, y_max], dtick=max(5, int(max_duration/5)))
    
    # Convert to JSON for the template
    graph_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
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
            
            # Use end_time if available, otherwise fallback to date with 00:00 time
            timestamp = ex.workout.end_time if ex.workout.end_time else datetime.combine(ex.workout.date, datetime.min.time())
            
            # Ensure distance is a numeric value
            distance = float(ex.distance) if ex.distance is not None else 0
            
            data.append({
                'date': timestamp.strftime('%Y-%m-%d %H:%M'),
                'timestamp': timestamp,
                'distance': distance,  # Use the explicitly converted numeric value
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
        # Create a completely new approach for plotting
        # Convert data to simple lists of numbers for x and y
        x_values = list(range(len(df)))
        y_values = [float(val) for val in df['distance'].values]
        
        # Debug: print the actual values being used for the graph
        print("DEBUG: Data values for cardio distance graph:")
        for i, (x, y, ts) in enumerate(zip(x_values, y_values, df['timestamp'])):
            print(f"DEBUG: {i}: x={x}, y={y} miles, ts={ts}")
        
        # Create the plot with numeric indices for x-axis
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=x_values,
            y=y_values,
            mode='lines+markers',
            name='Distance'
        ))
        
        # Add custom x-axis labels with the timestamps
        fig.update_layout(
            xaxis=dict(
                tickmode='array',
                tickvals=x_values,
                ticktext=[ts.strftime('%Y-%m-%d %H:%M') for ts in df['timestamp']]
            )
        )
        fig.update_layout(title=f'Cardio Distance Over Time - {cardio_name}')
        
        # Format the x-axis to show date and time
        fig.update_xaxes(tickformat='%Y-%m-%d %H:%M')
    
    # Add hover data if we have data
    if not df.empty:
        hover_data = []
        for i, row in df.iterrows():
            hover_data.append(
                f"<b>Date & Time:</b> {row['date']}<br>"
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
    
    # Set Y-axis to start at 0 and have appropriate range based on data
    if not df.empty:
        max_distance = max(y_values)  # Use the y_values list we created earlier
        # Add 10% padding to the top of the range
        y_max = max_distance * 1.1
        fig.update_yaxes(range=[0, y_max], dtick=max(0.5, round(max_distance/5, 1)))
    
    # Convert to JSON for the template
    graph_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    return graph_json
