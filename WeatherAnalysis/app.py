# Import the dependencies.
import numpy as np
import datetime as dt
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

from flask import Flask, jsonify



#################################################
# Database Setup
#################################################

engine = create_engine("sqlite:///../Resources/hawaii.sqlite")
# reflect an existing database into a new model
Base = automap_base()
# reflect the tables
Base.prepare(autoload_with=engine)

# Save references to each table
Measure = Base.classes.measurement
Station = Base.classes.station

# Create our session (link) from Python to the DB
session = Session(engine)

#################################################
# Flask Setup
#################################################
app = Flask(__name__)



#################################################
# Flask Routes
#################################################
@app.route('/')
def home():
    # List all the available routes.
    return (
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation - dictionary of precipitation by date of last year<br/>"
        f"/api/v1.0/stations - list of stations<br/>"
        f"/api/v1.0/tobs - list of temperature observations for most active station<br/>"
        f"/api/v1.0/start - min,max, and avg temperature from start date (must be in YYYY-MM-DD format)<br/>"
        f"/api/v1.0/start/end - min,max, and avg temperature from start date to end date (must be in YYYY-MM-DD format)"
    )

@app.route('/api/v1.0/precipitation')
def prcp():
    # Calculate the date one year from the last date in data set.
    current_date = session.query(Measure.date).order_by(Measure.date.desc()).first()[0]
    prev_year = dt.datetime.strftime(dt.datetime.strptime(current_date,'%Y-%m-%d') - dt.timedelta(days = 365),'%Y-%m-%d')

    # Perform a query to retrieve the data and precipitation scores
    date_prcp = session.query(Measure.date,Measure.prcp).\
        filter(Measure.date >= prev_year).\
        order_by(Measure.date.desc()).all()
    
    # Dictionary of tempeartures, key: date, value: list of recorded temperatures
    prec_dict = {}
    for i in date_prcp:
        if i[0] not in prec_dict:
            prec_dict[i[0]] = []
        prec_dict[i[0]].append(i[1])
    print('Successful precipitation query')
    session.close()
    return prec_dict

@app.route('/api/v1.0/stations')
def stations():
    # Query station id and name
    station_list = session.query(Station.station,Station.name).all()
    print('Successful stations query')
    session.close()
    return jsonify([(i[0],i[1]) for i in station_list])

@app.route('/api/v1.0/tobs')
def tobs():
    # Calculate the date one year from the last date in data set.
    current_date = session.query(Measure.date).order_by(Measure.date.desc()).first()[0]
    prev_year = dt.datetime.strftime(dt.datetime.strptime(current_date,'%Y-%m-%d') - dt.timedelta(days = 365),'%Y-%m-%d')

    # Order stations by number of occurrences
    active_stations = session.query(Measure.station,func.count(Measure.station)).group_by(Measure.station).order_by(func.count(Measure.station).desc()).all()

    # Find temperature observations of most active station
    station_name = active_stations[0][0]
    temps = session.query(Measure.tobs).filter(Measure.station == station_name).filter(Measure.date >= prev_year).all()
    print('Successful tobs query')
    session.close()
    return jsonify([i[0] for i in temps])

@app.route('/api/v1.0/<start>')
def temps_start(start):
    # Check if date is in right format YYYY-MM-DD
    try:
        dt.date.fromisoformat(start)
    except ValueError:
        return jsonify({"error": f"Date must be in YYYY-MM-DD format."})
    
    # Query based on date used
    temp_metrics = session.query(func.min(Measure.tobs),func.max(Measure.tobs),func.avg(Measure.tobs))\
        .filter(Measure.date >= start)\
        .all()
    print('Successful start date query')
    session.close()
    return jsonify([temp_metrics[0][0],temp_metrics[0][1],temp_metrics[0][2]])

@app.route('/api/v1.0/<start>/<end>')
def temps_start_end(start,end):
    # Check if date is in right format YYYY-MM-DD
    try:
        dt.date.fromisoformat(start)
        dt.date.fromisoformat(end)
        assert start < end
    except ValueError:
        return jsonify({"error": f"Date must be in YYYY-MM-DD format."})
    except AssertionError:
        return jsonify({"error": f"End date must be later than start date."})
    
    # Query based on date used
    temp_metrics = session.query(func.min(Measure.tobs),func.max(Measure.tobs),func.avg(Measure.tobs))\
        .filter(Measure.date >= start).filter(Measure.date <= end)\
        .all()
    print('Successful start-end date query')
    session.close()

    
    return jsonify([temp_metrics[0][0],temp_metrics[0][1],temp_metrics[0][2]])


if __name__ == '__main__':
    app.run(debug=True)