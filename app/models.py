from app import db
from datetime import datetime
from sqlalchemy.orm import relationship

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    workouts = relationship("Workout", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<User {self.name}>'

class Workout(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, default=datetime.utcnow().date)
    start_time = db.Column(db.DateTime, nullable=True)
    end_time = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="workouts")
    weight_exercises = relationship("WeightExercise", back_populates="workout", cascade="all, delete-orphan")
    cardio_exercises = relationship("CardioExercise", back_populates="workout", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<Workout {self.id} for User {self.user_id} on {self.date}>'

class WeightMachine(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    
    # Relationships
    exercises = relationship("WeightExercise", back_populates="machine")
    
    def __repr__(self):
        return f'<WeightMachine {self.name}>'

class CardioType(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    
    # Relationships
    exercises = relationship("CardioExercise", back_populates="cardio_type")
    
    def __repr__(self):
        return f'<CardioType {self.name}>'

class WeightExercise(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    workout_id = db.Column(db.Integer, db.ForeignKey('workout.id'), nullable=False)
    machine_id = db.Column(db.Integer, db.ForeignKey('weight_machine.id'), nullable=False)
    sets_reps_weight = db.Column(db.String(200), nullable=False)  # Format: "1x12 at 50 lbs, 2x15 at 20 lbs"
    seat_height = db.Column(db.String(50), nullable=True)
    other_parameters = db.Column(db.String(200), nullable=True)
    confidence = db.Column(db.String(20), default="medium")  # low, medium, high
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    workout = relationship("Workout", back_populates="weight_exercises")
    machine = relationship("WeightMachine", back_populates="exercises")
    
    def __repr__(self):
        return f'<WeightExercise {self.id} on {self.machine.name}>'
    
    @property
    def total_reps(self):
        """Calculate the total number of repetitions from the sets_reps_weight string."""
        total = 0
        sets = self.sets_reps_weight.split(',')
        for set_info in sets:
            set_info = set_info.strip()
            if 'x' in set_info and 'at' in set_info:
                try:
                    # Extract the sets and reps
                    sets_reps = set_info.split('at')[0].strip()
                    sets_count, reps_count = sets_reps.split('x')
                    total += int(sets_count) * int(reps_count)
                except (ValueError, IndexError):
                    pass
        return total
    
    @property
    def average_weight(self):
        """Calculate the weighted average weight from the sets_reps_weight string."""
        total_weight = 0
        total_reps = 0
        sets = self.sets_reps_weight.split(',')
        
        for set_info in sets:
            set_info = set_info.strip()
            if 'x' in set_info and 'at' in set_info:
                try:
                    # Extract the sets, reps, and weight
                    sets_reps, weight_part = set_info.split('at')
                    sets_reps = sets_reps.strip()
                    sets_count, reps_count = sets_reps.split('x')
                    
                    # Extract the weight value
                    weight = weight_part.strip()
                    weight_value = float(weight.split()[0])
                    
                    # Calculate weighted contribution
                    set_reps = int(sets_count) * int(reps_count)
                    total_reps += set_reps
                    total_weight += set_reps * weight_value
                except (ValueError, IndexError):
                    pass
        
        if total_reps > 0:
            return total_weight / total_reps
        return 0

class CardioExercise(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    workout_id = db.Column(db.Integer, db.ForeignKey('workout.id'), nullable=False)
    cardio_type_id = db.Column(db.Integer, db.ForeignKey('cardio_type.id'), nullable=False)
    duration = db.Column(db.String(10), nullable=True)  # Format: "MM:SS"
    distance = db.Column(db.Float, nullable=True)  # Miles
    calories = db.Column(db.Integer, nullable=True)
    incline = db.Column(db.Float, nullable=True)
    resistance = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    workout = relationship("Workout", back_populates="cardio_exercises")
    cardio_type = relationship("CardioType", back_populates="exercises")
    
    def __repr__(self):
        return f'<CardioExercise {self.id} on {self.cardio_type.name}>'
    
    @property
    def duration_minutes(self):
        """Convert duration string to minutes as a float."""
        if not self.duration:
            return 0
        
        try:
            minutes, seconds = self.duration.split(':')
            return float(minutes) + float(seconds) / 60
        except (ValueError, IndexError):
            return 0
