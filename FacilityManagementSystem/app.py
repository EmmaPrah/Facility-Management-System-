print("DEBUG: Executing app.py - Top of File Check - v1.0")
import psycopg2
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, g
from datetime import date, datetime, timedelta
import os
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from flask_mail import Mail, Message
import calendar
import logging

# ... (rest of the code remains the same until get_db() function)

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        if not DATABASE_URL:
            raise RuntimeError('DATABASE_URL environment variable not set')
        app.logger.debug("Creating new PostgreSQL DB connection")
        db = g._database = psycopg2.connect(DATABASE_URL)
    else:
        app.logger.debug("Using existing PostgreSQL DB connection from g")
    return db

# ... (rest of the code remains the same until init_db() function)

def init_db():
    app.logger.info("Attempting to initialize PostgreSQL database.")
    try:
        conn = get_db()
        app.logger.info("Database connection obtained for init_db.")
        schema_sql_content = ""
        with app.open_resource('schema_postgres.sql', mode='r') as f:
            schema_sql_content = f.read()
        cursor = conn.cursor()
        cursor.execute("BEGIN;")
        for statement in schema_sql_content.split(';'):
            stmt = statement.strip()
            if stmt:
                cursor.execute(stmt)
        conn.commit()
        cursor.close()
        app.logger.info("Database initialization operations completed successfully.")
    except Exception as e:
        app.logger.error(f"Error during database initialization: {e}", exc_info=True)

# ... (rest of the code remains the same until close_connection() function)

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        app.logger.debug("Closing PostgreSQL DB connection")
        db.close()
    if exception:
        app.logger.error(f"Exception in teardown: {exception}")

# ... (rest of the code remains the same)

# Update SQL parameter placeholders from ? to %s for psycopg2
# Update row handling to use cursor.description for dicts
# Update init_db to use schema_postgres.sql
# Update teardown logic for psycopg2
# Add error handling for missing DATABASE_URL

# ... (rest of the code remains the same)
            ]
            cursor.executemany("INSERT INTO cleaning_areas (name) VALUES (?)", default_areas)
            conn.commit() # Commit after inserting areas
            app.logger.info("Default cleaning_areas populated.")

            # Fetch area IDs correctly
            areas_map = {name: area_id for name, area_id in cursor.execute("SELECT name, id FROM cleaning_areas").fetchall()}
            app.logger.info(f"areas_map created: {areas_map}")

            default_tasks_data = [
                (areas_map.get('Reception Area'), 'Empty trash bins and refill bags'),
                (areas_map.get('Office Rooms'), 'Empty garbage bins & refill liners'),
                (areas_map.get('Restroom'), 'Empty & refill trash bins with new liners'),
                # Add more default tasks here, ensuring area_name exists in areas_map
            ]
            # Filter out tasks where area_id might be None if area name wasn't found
            valid_tasks = [(area_id, desc) for area_id, desc in default_tasks_data if area_id is not None]
            if valid_tasks:
                 cursor.executemany("INSERT INTO cleaning_tasks (area_id, description) VALUES (?, ?)", valid_tasks)
                 conn.commit() # Commit after inserting tasks
                 app.logger.info("Default cleaning_tasks populated and committed.")
            else:
                app.logger.warning("No valid default tasks to populate based on areas_map.")

        elif count_result is None:
            app.logger.warning("Failed to get count from cleaning_areas. Skipping population.")
        else:
            app.logger.info(f"cleaning_areas table count: {count_result[0]}. Skipping population.")

        # Populate facilities table if empty
        cursor.execute("SELECT COUNT(*) FROM facilities")
        facility_count_result = cursor.fetchone()
        if facility_count_result is not None and facility_count_result[0] == 0:
            app.logger.info("facilities table is empty. Populating default facilities.")
            default_facilities_data = [
                ('Main Office Building', 'Primary office space for administrative staff.', 'Operational'),
                ('Warehouse Unit A', 'Storage and logistics hub for incoming/outgoing goods.', 'Operational'),
                ('Conference Center', 'Facility for meetings, presentations, and events.', 'Operational'),
                ('Research Lab Complex', 'Dedicated labs for R&D activities.', 'Under Maintenance')
            ]
            cursor.executemany("INSERT INTO facilities (name, description, status) VALUES (?, ?, ?)", default_facilities_data)
            conn.commit()
            app.logger.info("Default facilities populated.")
        elif facility_count_result is None:
            app.logger.warning("Failed to get count from facilities. Skipping population.")
        else:
            app.logger.info(f"facilities table count: {facility_count_result[0]}. Skipping population.")
        
        app.logger.info("Database initialization operations completed successfully.")

    except sqlite3.Error as e:
        app.logger.error(f"SQLite error during database initialization: {e}", exc_info=True)
    except FileNotFoundError:
        app.logger.error("schema.sql not found. Ensure it's in the instance folder or accessible via open_resource.", exc_info=True)
    except Exception as e:
        app.logger.error(f"An unexpected error occurred during database initialization: {e}", exc_info=True)
    # Connection is managed by app context (g and teardown_appcontext)

# Initialize DB within app context
with app.app_context():
    app.logger.info("Global scope: Calling init_db within app_context.")
    init_db()
    app.logger.info("Global scope: init_db call finished.")

@app.route('/')
def index():
    app.logger.debug("Index route '/' called, rendering index.html.")
    try:
        return render_template('index.html')
    except Exception as e:
        app.logger.error(f"Error rendering index.html: {e}", exc_info=True)
        return f"Error rendering index.html: {e}", 500


@app.route('/dashboard')
def dashboard():
    app.logger.debug("Dashboard route '/dashboard' called, attempting to fetch data and render dashboard.html.")
    facilities_data = []
    try:
        db = get_db()
        cursor = db.cursor()
        # Fetch facilities, ensuring created_at is handled for display
        cursor.execute("SELECT id, name, description, status, created_at FROM facilities ORDER BY created_at DESC")
        rows = cursor.fetchall()
        for row in rows:
            created_at_str = row['created_at']
            try:
                created_at_formatted = datetime.strptime(created_at_str, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d %H:%M')
            except (ValueError, TypeError):
                created_at_formatted = created_at_str if created_at_str else 'N/A'
            
            facilities_data.append({
                'id': row['id'],
                'name': row['name'],
                'description': row['description'],
                'status': row['status'],
                'created_at': created_at_formatted
            })
        app.logger.info(f"Fetched {len(facilities_data)} facilities for the dashboard.")
        return render_template('dashboard.html', facilities=facilities_data)
    except sqlite3.Error as e:
        app.logger.error(f"Database error on dashboard: {e}", exc_info=True)
        flash(f"Error loading dashboard data: {e}", "danger")
        return render_template('dashboard.html', facilities=[], error=str(e)) # Render with empty data on DB error
    except Exception as e:
        app.logger.error(f"Unexpected error on dashboard: {e}", exc_info=True)
        flash("An unexpected error occurred while loading the dashboard.", "danger")
        return render_template('dashboard.html', facilities=[], error="An unexpected error occurred."), 500 # Render with empty data


@app.route('/cleaning-checklist')
def cleaning_checklist_page():
    app.logger.debug("Route '/cleaning-checklist' called to render template.")
    db = get_db()
    cursor = db.cursor()
    
    fetched_areas_for_dropdown = []
    areas_with_tasks_list = []
    today_str = date.today().strftime("%Y-%m-%d")
    
    try:
        cursor.execute("SELECT id, name FROM cleaning_areas ORDER BY name")
        fetched_areas_for_dropdown = cursor.fetchall()
        
        for area_row in fetched_areas_for_dropdown:
            area_id = area_row[0]
            area_name = area_row[1]
            
            cursor.execute("SELECT id, description FROM cleaning_tasks WHERE area_id = ? ORDER BY description", (area_id,))
            tasks_for_area = cursor.fetchall()
            
            tasks_list = [{'id': task[0], 'description': task[1]} for task in tasks_for_area]
            areas_with_tasks_list.append({'id': area_id, 'name': area_name, 'tasks': tasks_list})
            
        return render_template('cleaning_checklist.html', 
                               facilities=[{'id': area[0], 'name': area[1]} for area in fetched_areas_for_dropdown], 
                               areas_with_tasks=areas_with_tasks_list, 
                               today_date=today_str)
                               
    except sqlite3.Error as e:
        app.logger.error(f"Database error on cleaning checklist page: {e}", exc_info=True)
        flash(f"Error loading checklist data: {e}", "danger")
        return render_template('cleaning_checklist.html', facilities=[], areas_with_tasks=[], today_date=today_str, error=str(e))
    except Exception as e:
        app.logger.error(f"Unexpected error on cleaning checklist page: {e}", exc_info=True)
        flash(f"An unexpected error occurred: {e}", "danger")
        # Fallback to rendering the page with minimal data or a clear error message
        return render_template('cleaning_checklist.html', facilities=[], areas_with_tasks=[], today_date=today_str, error="An unexpected error occurred while loading data."), 500

@app.route('/maintenance')
def maintenance_management_page():
    app.logger.debug("Route '/maintenance' called to render manage_maintenance.html.")
    maintenance_requests_data = []
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            SELECT mr.id, f.name AS facility_name, mr.description AS issue_description, 
                   mr.priority, mr.reported_at, mr.status
            FROM maintenance_requests mr
            JOIN facilities f ON mr.facility_id = f.id
            ORDER BY mr.reported_at DESC
        """)
        rows = cursor.fetchall()
        for row in rows:
            maintenance_requests_data.append({
                'id': row[0],
                'facility_name': row[1],
                'issue_description': row[2],
                'priority': row[3],
                'reported_at': datetime.strptime(row[4], '%Y-%m-%d %H:%M:%S') if row[4] else None,
                'status': row[5]
            })
        app.logger.info(f"Fetched {len(maintenance_requests_data)} maintenance requests from database.")
        return render_template('manage_maintenance.html', maintenance_requests=maintenance_requests_data)
    except Exception as e:
        app.logger.error(f"Error rendering manage_maintenance.html: {e}", exc_info=True)
        flash(f"Error loading maintenance page: {e}", "danger")
        # Fallback or redirect if template rendering fails
        return "Error loading maintenance page. Please try again later.", 500


@app.route('/facilities/add', methods=['GET', 'POST'], endpoint='add_facility') # Added endpoint for clarity with url_for
def add_facility():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        status = request.form.get('status')

        if not name or not description or not status:
            flash('All fields are required.', 'danger')
            return render_template('add_facility.html'), 400

        try:
            db = get_db()
            cursor = db.cursor()
            cursor.execute(
                "INSERT INTO facilities (name, description, status) VALUES (?, ?, ?)",
                (name, description, status)
            )
            db.commit()
            flash(f'Facility "{name}" added successfully!', 'success')
            app.logger.info(f"Facility '{name}' added successfully.")
            return redirect(url_for('dashboard'))
        except sqlite3.Error as e:
            flash(f'Database error: {e}', 'danger')
            app.logger.error(f"Database error when adding facility: {e}", exc_info=True)
            # It's good practice to rollback on error, though with autocommit or single statements it might not be strictly necessary
            # if db: db.rollback()
            return render_template('add_facility.html', name=name, description=description, status=status), 500
        except Exception as e:
            flash(f'An unexpected error occurred: {e}', 'danger')
            app.logger.error(f"Unexpected error when adding facility: {e}", exc_info=True)
            return render_template('add_facility.html', name=name, description=description, status=status), 500
    
    # For GET request
    return render_template('add_facility.html')


@app.route('/facilities', methods=['GET'])
def manage_facilities_page():
    app.logger.debug("Route '/facilities' called to render manage_facilities.html.")
    facilities_data = []
    try:
        db = get_db()
        cursor = db.cursor()
        # Ensure created_at is fetched correctly; assuming it's stored as TEXT in 'YYYY-MM-DD HH:MM:SS' format
        cursor.execute("SELECT id, name, description, status, created_at FROM facilities ORDER BY name")
        rows = cursor.fetchall()
        for row in rows:
            created_at_str = row['created_at']
            try:
                # Attempt to parse if it's a full datetime string, otherwise handle as is or set to N/A
                created_at_formatted = datetime.strptime(created_at_str, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d %H:%M')
            except (ValueError, TypeError):
                # If parsing fails (e.g., it's already formatted or None), use as is or default
                created_at_formatted = created_at_str if created_at_str else 'N/A'
            
            facilities_data.append({
                'id': row['id'],
                'name': row['name'],
                'description': row['description'],
                'status': row['status'],
                'created_at': datetime.strptime(row['created_at'], '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d %H:%M') if row['created_at'] else 'N/A'
            })
        app.logger.info(f"Fetched {len(facilities_data)} facilities from database.")
    except sqlite3.Error as e:
        app.logger.error(f"Database error on manage facilities page: {e}", exc_info=True)
        flash(f"Error loading facilities: {e}", "danger")
    except Exception as e:
        app.logger.error(f"Unexpected error on manage facilities page: {e}", exc_info=True)
        flash("An unexpected error occurred while loading facilities.", "danger")
    
    return render_template('manage_facilities.html', facilities=facilities_data)


@app.route('/add_maintenance_request', methods=['GET', 'POST'])
def add_maintenance_request_page():
    app.logger.debug(f"Route '/add_maintenance_request' called with method {request.method}")
    if request.method == 'POST':
        facility_id = request.form.get('facility_id')
        issue_description = request.form.get('issue_description')
        priority = request.form.get('priority')

        if not facility_id or not issue_description or not priority:
            flash('All fields are required.', 'danger')
            # Re-render form with existing values if needed, or simply redirect
            # For simplicity, redirecting back to form. Ideally, preserve entered data.
            return redirect(url_for('add_maintenance_request_page'))

        try:
            db = get_db()
            cursor = db.cursor()
            cursor.execute(
                "INSERT INTO maintenance_requests (facility_id, description, priority) VALUES (?, ?, ?)",
                (facility_id, issue_description, priority)
            )
            db.commit()
            app.logger.info(f"New maintenance request saved: Facility ID='{facility_id}', Issue='{issue_description}', Priority='{priority}'")
            flash('New maintenance request submitted successfully!', 'success')
            return redirect(url_for('maintenance_management_page'))
        except sqlite3.Error as e:
            app.logger.error(f"Database error saving maintenance request: {e}", exc_info=True)
            flash('Failed to submit maintenance request due to a database error.', 'danger')
            # Redirect back to the form, ideally with preserved data
            return redirect(url_for('add_maintenance_request_page'))
        except Exception as e:
            app.logger.error(f"Unexpected error saving maintenance request: {e}", exc_info=True)
            flash('An unexpected error occurred. Please try again.', 'danger')
            return redirect(url_for('add_maintenance_request_page'))
    
    # For GET request, render the form page
    db = get_db()
    cursor = db.cursor()
    facilities = []
    try:
        cursor.execute("SELECT id, name FROM facilities ORDER BY name") # Changed cleaning_areas to facilities
        facilities = [{'id': row[0], 'name': row[1]} for row in cursor.fetchall()]
    except sqlite3.Error as e:
        app.logger.error(f"Database error fetching facilities for add_maintenance_request form: {e}", exc_info=True)
        flash('Could not load facility list for the form.', 'danger')
    
    return render_template('add_maintenance_request.html', facilities=facilities) # We will create this template next

@app.route('/api/maintenance_requests/<int:request_id>/status', methods=['PUT'])
def update_maintenance_request_status(request_id):
    app.logger.debug(f"API call to update status for maintenance request ID: {request_id}")
    data = request.get_json()
    new_status = data.get('status')

    if not new_status:
        app.logger.warning(f"API update status: 'status' field missing in request for ID {request_id}.")
        return jsonify({'error': 'Missing status field'}), 400

    valid_statuses = ['Pending', 'In Progress', 'Completed', 'Cancelled'] # Add any other valid statuses
    if new_status not in valid_statuses:
        app.logger.warning(f"API update status: Invalid status '{new_status}' for ID {request_id}.")
        return jsonify({'error': f'Invalid status: {new_status}. Must be one of {valid_statuses}'}), 400

    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT id FROM maintenance_requests WHERE id = ?", (request_id,))
        request_exists = cursor.fetchone()

        if not request_exists:
            app.logger.warning(f"API update status: Maintenance request ID {request_id} not found.")
            return jsonify({'error': 'Maintenance request not found'}), 404

        cursor.execute(
            "UPDATE maintenance_requests SET status = ? WHERE id = ?",
            (new_status, request_id)
        )
        db.commit()
        app.logger.info(f"Successfully updated status for maintenance request ID {request_id} to '{new_status}'.")
        return jsonify({'success': True, 'message': 'Status updated successfully', 'new_status': new_status}), 200
    except sqlite3.Error as e:
        db.rollback() # Rollback in case of error
        app.logger.error(f"API update status: Database error for ID {request_id}: {e}", exc_info=True)
        return jsonify({'error': 'Database error occurred'}), 500
    except Exception as e:
        db.rollback() # Rollback in case of error
        app.logger.error(f"API update status: Unexpected error for ID {request_id}: {e}", exc_info=True)
        return jsonify({'error': 'An unexpected error occurred'}), 500


@app.route('/api/cleaning_log_entries', methods=['GET'])
def get_cleaning_log_entries():
    facility_id = request.args.get('facility_id')
    date_str = request.args.get('date')
    app.logger.debug(f"API GET /api/cleaning_log_entries called with facility_id={facility_id}, date={date_str}")

    if not facility_id or not date_str:
        app.logger.warning("API GET /api/cleaning_log_entries: Missing facility_id or date parameter.")
        return jsonify({'success': False, 'message': 'Missing facility_id or date parameter'}), 400

    try:
        # Validate date format if necessary, for now assuming YYYY-MM-DD
        # Fetch tasks for the given facility (area)
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT id, description FROM cleaning_tasks WHERE area_id = ? ORDER BY description", (facility_id,))
        tasks = cursor.fetchall()

        log_entries_for_date = {}
        # Fetch existing log entries for these tasks on the given date
        # Note: facility_id in cleaning_log_entries refers to the main 'facilities' table in the schema, 
        # but here we are using it as cleaning_area_id. This needs to be consistent or schema adjusted.
        # For now, assuming the JS sends cleaning_area_id as facility_id for this API.
        for task in tasks:
            task_id = task[0]
            cursor.execute("""
                SELECT status, notes FROM cleaning_log_entries 
                WHERE task_id = ? AND DATE(completed_at) = ? 
                  AND facility_id = ?  -- This facility_id should be cleaning_area_id based on context
            """, (task_id, date_str, facility_id))
            entry = cursor.fetchone()
            if entry:
                log_entries_for_date[task_id] = {'status': entry[0], 'notes': entry[1]}
            else:
                log_entries_for_date[task_id] = {'status': 'Pending', 'notes': ''}
        
        # Prepare response
        response_tasks = []
        for task_row in tasks:
            task_id = task_row[0]
            description = task_row[1]
            entry_data = log_entries_for_date.get(task_id, {'status': 'Pending', 'notes': ''})
            response_tasks.append({
                'id': task_id,
                'description': description,
                'status': entry_data['status'],
                'notes': entry_data['notes']
            })
        
        app.logger.info(f"API GET /api/cleaning_log_entries: Successfully fetched {len(response_tasks)} tasks for facility_id={facility_id}, date={date_str}")
        return jsonify({'success': True, 'tasks': response_tasks})

    except sqlite3.Error as e:
        app.logger.error(f"API GET /api/cleaning_log_entries: Database error for facility_id={facility_id}, date={date_str}: {e}", exc_info=True)
        return jsonify({'success': False, 'message': 'Database error occurred'}), 500
    except Exception as e:
        app.logger.error(f"API GET /api/cleaning_log_entries: Unexpected error for facility_id={facility_id}, date={date_str}: {e}", exc_info=True)
        return jsonify({'success': False, 'message': 'An unexpected error occurred'}), 500


@app.route('/api/cleaning_log', methods=['POST'])
def save_cleaning_log():
    data = request.get_json()
    facility_id = data.get('facility_id') # This is actually cleaning_area_id
    date_str = data.get('date')
    entries = data.get('entries')

    app.logger.debug(f"API POST /api/cleaning_log: facility_id={facility_id}, date={date_str}, entries_count={len(entries) if entries else 0}")

    if not facility_id or not date_str or entries is None:
        app.logger.warning("API POST /api/cleaning_log: Missing facility_id, date, or entries.")
        return jsonify({'success': False, 'message': 'Missing facility_id, date, or entries'}), 400

    try:
        db = get_db()
        cursor = db.cursor()

        for entry in entries:
            task_id = entry.get('task_id')
            status = entry.get('status')
            notes = entry.get('notes', '') # Default to empty string if notes are missing

            if not task_id or not status:
                app.logger.warning(f"API POST /api/cleaning_log: Skipping entry due to missing task_id or status. Entry: {entry}")
                continue # Skip this entry and process others

            # Check if an entry already exists for this task, facility (area), and date
            # The 'completed_at' field stores full datetime, so we compare the date part.
            # For simplicity, we're using the date_str directly. If completed_at is just DATE, it's simpler.
            # Given schema uses DATETIME DEFAULT CURRENT_TIMESTAMP, we'll assume date_str is sufficient for this logic.
            # A more robust way would be to store date separately or query date(completed_at).
            
            # For cleaning_log_entries, facility_id IS the cleaning_area_id due to schema change.
            # completed_at should store the specific date of the checklist for querying.
            # We will store date_str combined with current time for completed_at when inserting/updating.
            # For querying, we will use DATE(completed_at) = date_str.
            
            completed_at_datetime_str = f"{date_str} {datetime.now().strftime('%H:%M:%S')}"

            cursor.execute("""
                SELECT id FROM cleaning_log_entries 
                WHERE task_id = ? AND facility_id = ? AND DATE(completed_at) = ?
            """, (task_id, facility_id, date_str))
            existing_entry = cursor.fetchone()

            if existing_entry:
                # Update existing entry
                app.logger.debug(f"API POST /api/cleaning_log: Updating entry for task_id={task_id}, facility_id={facility_id}, date={date_str}")
                cursor.execute("""
                    UPDATE cleaning_log_entries 
                    SET status = ?, notes = ?, completed_at = ? 
                    WHERE id = ?
                """, (status, notes, completed_at_datetime_str, existing_entry[0]))
            else:
                # Insert new entry
                app.logger.debug(f"API POST /api/cleaning_log: Inserting new entry for task_id={task_id}, facility_id={facility_id}, date={date_str}")
                cursor.execute("""
                    INSERT INTO cleaning_log_entries (facility_id, task_id, status, notes, completed_at) 
                    VALUES (?, ?, ?, ?, ?)
                """, (facility_id, task_id, status, notes, completed_at_datetime_str))
        
        db.commit()
        app.logger.info(f"API POST /api/cleaning_log: Successfully saved/updated checklist for facility_id={facility_id}, date={date_str}")
        return jsonify({'success': True, 'message': 'Checklist saved successfully'}), 200

    except sqlite3.Error as e:
        db.rollback()
        app.logger.error(f"API POST /api/cleaning_log: Database error for facility_id={facility_id}, date={date_str}: {e}", exc_info=True)
        return jsonify({'success': False, 'message': 'Database error occurred'}), 500
    except Exception as e:
        db.rollback()
        app.logger.error(f"API POST /api/cleaning_log: Unexpected error for facility_id={facility_id}, date={date_str}: {e}", exc_info=True)
        return jsonify({'success': False, 'message': 'An unexpected error occurred'}), 500


@app.route('/expenditures')
def expenditures_page():
    app.logger.debug("Route '/expenditures' called.")
    db = get_db()
    cursor = db.cursor()
    expenditures_data = []
    try:
        # Fetch expenditures, joining with facilities to get facility name
        # Using LEFT JOIN in case facility_id is NULL
        cursor.execute("""
            SELECT e.id, e.expenditure_date, e.category, e.description, e.amount, 
                   e.vendor, e.facility_id, e.receipt_reference, e.notes, e.created_at, 
                   f.name AS facility_name
            FROM expenditures e
            LEFT JOIN facilities f ON e.facility_id = f.id
            ORDER BY e.expenditure_date DESC, e.created_at DESC
        """)
        rows = cursor.fetchall()
        for row in rows:
            expenditures_data.append({
                'id': row[0],
                'expenditure_date': row[1], # Already a date string from DB
                'category': row[2],
                'description': row[3],
                'amount': row[4],
                'vendor': row[5],
                'facility_id': row[6],
                'receipt_reference': row[7],
                'notes': row[8],
                'created_at': row[9], # Already a timestamp string from DB
                'facility_name': row[10]
            })
        app.logger.info(f"Fetched {len(expenditures_data)} expenditures from database.")
    except sqlite3.Error as e:
        app.logger.error(f"Database error fetching expenditures: {e}", exc_info=True)
        flash('Failed to load expenditures due to a database error.', 'danger')
    except Exception as e:
        app.logger.error(f"Unexpected error fetching expenditures: {e}", exc_info=True)
        flash('An unexpected error occurred while loading expenditures.', 'danger')
        
    return render_template('manage_expenditures.html', expenditures=expenditures_data)


@app.route('/add_expenditure', methods=['GET', 'POST'])
def add_expenditure_page():
    app.logger.debug(f"Route '/add_expenditure' called with method {request.method}")
    db = get_db()
    cursor = db.cursor()

    if request.method == 'POST':
        try:
            expenditure_date = request.form.get('expenditure_date')
            category = request.form.get('category')
            description = request.form.get('description')
            amount_str = request.form.get('amount')
            vendor = request.form.get('vendor')
            facility_id_str = request.form.get('facility_id')
            receipt_reference = request.form.get('receipt_reference')
            notes = request.form.get('notes')
            buyer = request.form.get('buyer')
            means_of_payment = request.form.get('means_of_payment')

            # Basic validation
            if not all([expenditure_date, category, description, amount_str]):
                flash('Expenditure Date, Category, Description, and Amount are required.', 'danger')
                # Fetch facilities again for rendering the form with an error
                cursor.execute("SELECT id, name FROM facilities ORDER BY name")
                facilities_for_dropdown = cursor.fetchall()
                return render_template('add_expenditure.html', 
                                       facilities=facilities_for_dropdown,
                                       expenditure_categories=expenditure_items_data.keys(),
                                       expenditure_items_data=expenditure_items_data,
                                       payment_means_options=payment_means_options,
                                       form_data=request.form), 400
            
            try:
                amount = float(amount_str)
            except ValueError:
                flash('Invalid amount format.', 'danger')
                cursor.execute("SELECT id, name FROM facilities ORDER BY name")
                facilities_for_dropdown = cursor.fetchall()
                return render_template('add_expenditure.html', 
                                       facilities=facilities_for_dropdown,
                                       expenditure_categories=expenditure_items_data.keys(),
                                       expenditure_items_data=expenditure_items_data,
                                       payment_means_options=payment_means_options,
                                       form_data=request.form), 400

            facility_id = int(facility_id_str) if facility_id_str else None

            cursor.execute("""
                INSERT INTO expenditures (expenditure_date, category, description, amount, vendor, facility_id, receipt_reference, notes, buyer, means_of_payment)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (expenditure_date, category, description, amount, vendor, facility_id, receipt_reference, notes, buyer, means_of_payment))
            db.commit()
            app.logger.info(f"New expenditure added: Category='{category}', Amount={amount}")
            flash('Expenditure added successfully!', 'success')
            return redirect(url_for('expenditures_page'))
        
        except sqlite3.Error as e:
            db.rollback()
            app.logger.error(f"Database error while adding expenditure: {e}", exc_info=True)
            flash(f'Database error: {e}', 'danger')
        except Exception as e:
            db.rollback()
            app.logger.error(f"Unexpected error while adding expenditure: {e}", exc_info=True)
            flash('An unexpected error occurred while adding the expenditure.', 'danger')
    
    # For GET request or if POST failed and needs to re-render form
    cursor.execute("SELECT id, name FROM facilities ORDER BY name")
    facilities_for_dropdown = cursor.fetchall()
    return render_template('add_expenditure.html', 
                           facilities=facilities_for_dropdown,
                           expenditure_categories=expenditure_items_data.keys(),
                           expenditure_items_data=expenditure_items_data,
                           payment_means_options=payment_means_options)


@app.route('/edit_expenditure/<int:expenditure_id>', methods=['GET', 'POST'])
def edit_expenditure_page(expenditure_id):
    app.logger.debug(f"Route '/edit_expenditure/{expenditure_id}' called with method {request.method}")
    db = get_db()
    cursor = db.cursor()

    if request.method == 'POST':
        expenditure_date = request.form.get('expenditure_date')
        category = request.form.get('category')
        description = request.form.get('description')
        amount_str = request.form.get('amount')
        vendor = request.form.get('vendor')
        facility_id_str = request.form.get('facility_id')
        receipt_reference = request.form.get('receipt_reference')
        notes = request.form.get('notes')
        buyer = request.form.get('buyer')
        means_of_payment = request.form.get('means_of_payment')

        # Basic Validation
        if not expenditure_date or not category or not description or not amount_str:
            flash('Expenditure Date, Category, Description, and Amount are required fields.', 'danger')
            # Need to re-fetch data for the form if validation fails on POST
            cursor.execute("SELECT * FROM expenditures WHERE id = ?", (expenditure_id,))
            expenditure = cursor.fetchone()
            if not expenditure:
                app.logger.error(f"Expenditure with ID {expenditure_id} not found on POST validation fail.")
                flash('Expenditure not found.', 'danger')
                return redirect(url_for('expenditures_page'))
            
            exp_dict = dict(zip([column[0] for column in cursor.description], expenditure))
            
            facilities_list = []
            try:
                cursor.execute("SELECT id, name FROM facilities ORDER BY name")
                facilities_list = [{'id': row[0], 'name': row[1]} for row in cursor.fetchall()]
            except sqlite3.Error as e:
                app.logger.error(f"Database error fetching facilities for edit form (POST validation fail): {e}", exc_info=True)
                flash('Could not load facility list for the form.', 'danger')
            return render_template('edit_expenditure.html', 
                                   expenditure=exp_dict, 
                                   facilities=facilities_list,
                                   expenditure_categories=expenditure_items_data.keys(),
                                   expenditure_items_data=expenditure_items_data,
                                   payment_means_options=payment_means_options,
                                   form_data=request.form)

        try:
            amount = float(amount_str)
        except ValueError:
            flash('Invalid amount. Please enter a valid number.', 'danger')
            # Re-fetch data for the form
            cursor.execute("SELECT * FROM expenditures WHERE id = ?", (expenditure_id,))
            expenditure = cursor.fetchone()
            if not expenditure:
                app.logger.error(f"Expenditure with ID {expenditure_id} not found on POST amount validation fail.")
                flash('Expenditure not found.', 'danger')
                return redirect(url_for('expenditures_page'))
            exp_dict = dict(zip([column[0] for column in cursor.description], expenditure))
            facilities_list = []
            try:
                cursor.execute("SELECT id, name FROM facilities ORDER BY name")
                facilities_list = [{'id': row[0], 'name': row[1]} for row in cursor.fetchall()]
            except sqlite3.Error as e:
                app.logger.error(f"Database error fetching facilities for edit form (POST amount validation fail): {e}", exc_info=True)
            return render_template('edit_expenditure.html', 
                                   expenditure=exp_dict, 
                                   facilities=facilities_list,
                                   expenditure_categories=expenditure_items_data.keys(),
                                   expenditure_items_data=expenditure_items_data,
                                   payment_means_options=payment_means_options,
                                   form_data=request.form)

        facility_id = int(facility_id_str) if facility_id_str else None

        try:
            cursor.execute("""
                UPDATE expenditures
                SET expenditure_date = ?, category = ?, description = ?, amount = ?, vendor = ?, facility_id = ?, receipt_reference = ?, notes = ?, buyer = ?, means_of_payment = ?
                WHERE id = ?
            """, (expenditure_date, category, description, amount, vendor, facility_id, receipt_reference, notes, buyer, means_of_payment, expenditure_id))
            db.commit()
            app.logger.info(f"Expenditure ID {expenditure_id} updated successfully.")
            flash('Expenditure updated successfully!', 'success')
            return redirect(url_for('expenditures_page'))
        except sqlite3.Error as e:
            db.rollback()
            app.logger.error(f"Database error updating expenditure ID {expenditure_id}: {e}", exc_info=True)
            flash('Failed to update expenditure due to a database error.', 'danger')
        except Exception as e:
            db.rollback()
            app.logger.error(f"Unexpected error updating expenditure ID {expenditure_id}: {e}", exc_info=True)
            flash('An unexpected error occurred while updating the expenditure.', 'danger')

    # GET Request
    try:
        cursor.execute("SELECT * FROM expenditures WHERE id = ?", (expenditure_id,))
        expenditure = cursor.fetchone()

        if not expenditure:
            app.logger.warning(f"Edit expenditure: Expenditure ID {expenditure_id} not found.")
            flash('Expenditure not found.', 'danger')
            return redirect(url_for('expenditures_page'))

        # Convert row to dict for easier template access
        exp_dict = dict(zip([column[0] for column in cursor.description], expenditure))
        # Format date for HTML date input (YYYY-MM-DD)
        if isinstance(exp_dict.get('expenditure_date'), str):
             try:
                dt_obj = datetime.strptime(exp_dict['expenditure_date'], '%Y-%m-%d %H:%M:%S')
                exp_dict['expenditure_date'] = dt_obj.strftime('%Y-%m-%d')
             except ValueError:
                # if already YYYY-MM-DD or other format, try to use as is or log error
                pass # Keep original if parsing fails, or handle error
        elif isinstance(exp_dict.get('expenditure_date'), date): # if it's a date object
            exp_dict['expenditure_date'] = exp_dict['expenditure_date'].strftime('%Y-%m-%d')

        facilities_list = []
        try:
            cursor.execute("SELECT id, name FROM facilities ORDER BY name")
            facilities_list = [{'id': row[0], 'name': row[1]} for row in cursor.fetchall()]
        except sqlite3.Error as e:
            app.logger.error(f"Database error fetching facilities for edit form (GET): {e}", exc_info=True)
            flash('Could not load facility list for the form.', 'danger')
            # Optionally, decide if you want to redirect or render with empty facilities

        return render_template('edit_expenditure.html', 
                               expenditure=exp_dict, 
                               facilities=facilities_list,
                               expenditure_categories=expenditure_items_data.keys(),
                               expenditure_items_data=expenditure_items_data,
                               payment_means_options=payment_means_options)

    except sqlite3.Error as e:
        app.logger.error(f"Database error fetching expenditure ID {expenditure_id} for edit: {e}", exc_info=True)
        flash('Failed to load expenditure details due to a database error.', 'danger')
        return redirect(url_for('expenditures_page'))
    except Exception as e:
        app.logger.error(f"Unexpected error fetching expenditure ID {expenditure_id} for edit: {e}", exc_info=True)
        flash('An unexpected error occurred while loading the expenditure for editing.', 'danger')
        return redirect(url_for('expenditures_page'))


@app.route('/receipt/<int:expenditure_id>')
def generate_receipt(expenditure_id):
    app.logger.debug(f"Route '/receipt/{expenditure_id}' called")
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("""
            SELECT e.*, f.name as facility_name
            FROM expenditures e
            LEFT JOIN facilities f ON e.facility_id = f.id
            WHERE e.id = ?
        """, (expenditure_id,))
        expenditure_data = cursor.fetchone()

        if not expenditure_data:
            app.logger.warning(f"Receipt generation: Expenditure ID {expenditure_id} not found.")
            flash('Expenditure not found, cannot generate receipt.', 'danger')
            return redirect(url_for('expenditures_page'))

        expenditure = dict(zip([column[0] for column in cursor.description], expenditure_data))
        
        # Format date for display (e.g., Month Day, Year)
        original_date_val = expenditure.get('expenditure_date')
        expenditure['expenditure_date_formatted'] = 'N/A' # Default value

        if original_date_val:
            dt_obj = None
            try:
                if isinstance(original_date_val, str):
                    try:
                        dt_obj = datetime.strptime(original_date_val, '%Y-%m-%d')
                    except ValueError:
                        app.logger.debug(f"Date '{original_date_val}' for exp ID {expenditure_id} not in YYYY-MM-DD, trying YYYY-MM-DD HH:MM:SS")
                        dt_obj = datetime.strptime(original_date_val, '%Y-%m-%d %H:%M:%S')
                elif isinstance(original_date_val, datetime): # Handles datetime objects
                    dt_obj = original_date_val
                elif isinstance(original_date_val, date): # Handles date objects
                    # Convert date to datetime for consistency, though strftime works on date too
                    dt_obj = datetime(original_date_val.year, original_date_val.month, original_date_val.day)
                else:
                    app.logger.warning(f"Expenditure date for ID {expenditure_id} is of unexpected type: {type(original_date_val)}. Value: '{original_date_val}'")
                    # Fallback to string representation if type is unexpected and not parsable
                    expenditure['expenditure_date_formatted'] = str(original_date_val)
                
                if dt_obj:
                    expenditure['expenditure_date_formatted'] = dt_obj.strftime('%B %d, %Y')
                # If dt_obj is None here, it means it was an unexpected type and str() was used, or original_date_val was empty after all.

            except ValueError as ve: # Catches strptime errors
                app.logger.warning(f"Could not parse date string for expenditure ID {expenditure_id}. Value: '{original_date_val}'. Error: {ve}")
                expenditure['expenditure_date_formatted'] = str(original_date_val) # Fallback to original string value if parsing fails
            except Exception as ex:
                app.logger.error(f"Unexpected error during date formatting for expenditure ID {expenditure_id}. Value: '{original_date_val}'. Error: {ex}", exc_info=True)
                expenditure['expenditure_date_formatted'] = str(original_date_val) # Fallback in case of other errors
        
        # Final check to ensure 'expenditure_date_formatted' is set, if original_date_val was None or empty, it's already 'N/A'
        if not expenditure.get('expenditure_date_formatted') and original_date_val:
             expenditure['expenditure_date_formatted'] = str(original_date_val) # Should not be typically hit if logic above is correct

        current_timestamp = datetime.now()
        return render_template('receipt.html', expenditure=expenditure, current_timestamp=current_timestamp)

    except sqlite3.Error as e:
        app.logger.error(f"Database error fetching expenditure ID {expenditure_id} for receipt: {e}", exc_info=True)
        flash('Failed to generate receipt due to a database error.', 'danger')
        return redirect(url_for('expenditures_page'))
    except Exception as e:
        app.logger.error(f"Unexpected error generating receipt for expenditure ID {expenditure_id}: {e}", exc_info=True)
        flash(f'An unexpected error occurred while generating the receipt: {str(e)}', 'danger')
        return redirect(url_for('expenditures_page'))


def get_previous_week_dates():
    today = date.today()
    # Calculate days to subtract to get to the previous Monday
    # today.weekday(): Monday is 0 and Sunday is 6
    days_to_last_monday = today.weekday() + 7  # Go to start of *last* week's Monday
    last_monday = today - timedelta(days=days_to_last_monday)
    last_sunday = last_monday + timedelta(days=6)
    return last_monday, last_sunday

def get_expenditures_for_week(start_date, end_date):
    # Placeholder for fetching expenditures
    app.logger.debug(f"Fetching expenditures from {start_date} to {end_date}")
    db = get_db()
    cursor = db.cursor()
    # Query to fetch expenditures including facility name
    cursor.execute("""
        SELECT e.*, f.name as facility_name
        FROM expenditures e
        LEFT JOIN facilities f ON e.facility_id = f.id
        WHERE e.expenditure_date BETWEEN ? AND ?
        ORDER BY e.expenditure_date DESC, e.created_at DESC
    """, (start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')))
    expenditures = [dict(zip([column[0] for column in cursor.description], row)) for row in cursor.fetchall()]
    app.logger.info(f"Fetched {len(expenditures)} expenditures for the week.")
    return expenditures

def get_maintenance_for_week(start_date, end_date):
    # Placeholder for fetching maintenance requests
    app.logger.debug(f"Fetching maintenance requests from {start_date} to {end_date}")
    db = get_db()
    cursor = db.cursor()
    # Query to fetch maintenance requests including facility name
    cursor.execute("""
        SELECT mr.*, f.name as facility_name
        FROM maintenance_requests mr
        JOIN facilities f ON mr.facility_id = f.id
        WHERE date(mr.reported_at) BETWEEN ? AND ?
        ORDER BY mr.reported_at DESC
    """, (start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')))
    maintenance_requests = [dict(zip([column[0] for column in cursor.description], row)) for row in cursor.fetchall()]
    app.logger.info(f"Fetched {len(maintenance_requests)} maintenance requests for the week.")
    return maintenance_requests

def get_cleaning_logs_for_week(start_date, end_date):
    # Placeholder for fetching cleaning logs
    app.logger.debug(f"Fetching cleaning logs from {start_date} to {end_date}")
    db = get_db()
    cursor = db.cursor()
    # Query to fetch cleaning logs including facility and task details
    cursor.execute("""
        SELECT cle.*, f.name as facility_name, ca.name as area_name, ct.description as task_description
        FROM cleaning_log_entries cle
        JOIN facilities f ON cle.facility_id = f.id  -- Assuming cleaning_log_entries.facility_id refers to facilities.id
        JOIN cleaning_tasks ct ON cle.task_id = ct.id
        JOIN cleaning_areas ca ON ct.area_id = ca.id
        WHERE date(cle.completed_at) BETWEEN ? AND ?
        ORDER BY cle.completed_at DESC
    """, (start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')))
    cleaning_logs = [dict(zip([column[0] for column in cursor.description], row)) for row in cursor.fetchall()]
    app.logger.info(f"Fetched {len(cleaning_logs)} cleaning logs for the week.")
    return cleaning_logs

@app.route('/reports/weekly')
def weekly_report_page():
    app.logger.info("Weekly report page accessed.")
    try:
        start_of_week, end_of_week = get_previous_week_dates()
        
        expenditures = get_expenditures_for_week(start_of_week, end_of_week)
        maintenance_requests = get_maintenance_for_week(start_of_week, end_of_week)
        cleaning_logs = get_cleaning_logs_for_week(start_of_week, end_of_week)
        
        report_title = f"Weekly Report for {start_of_week.strftime('%B %d, %Y')} to {end_of_week.strftime('%B %d, %Y')}"
        
        return render_template('weekly_report.html', 
                               report_title=report_title,
                               expenditures=expenditures, 
                               maintenance_requests=maintenance_requests, 
                               cleaning_logs=cleaning_logs, 
                               start_date=start_of_week, 
                               end_date=end_of_week)
    except Exception as e:
        app.logger.error(f"Error generating weekly report: {e}", exc_info=True)
        flash('An error occurred while generating the weekly report. Please try again later.', 'danger')
        return redirect(url_for('dashboard'))


# --- Date Helper Functions for Custom Reports ---

def get_date_range_for_daily(selected_date_str):
    """Returns the selected date as start and end date objects."""
    try:
        report_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
        return report_date, report_date
    except ValueError:
        app.logger.error(f"Invalid date format for daily report: {selected_date_str}")
        return None, None

def get_date_range_for_weekly(selected_date_str):
    """Calculates the start (Monday) and end (Sunday) of the week for a given date string."""
    try:
        selected_dt = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
        start_of_week = selected_dt - timedelta(days=selected_dt.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        return start_of_week, end_of_week
    except ValueError:
        app.logger.error(f"Invalid date format for weekly range: {selected_date_str}")
        return None, None

def get_date_range_for_monthly(selected_month_str):
    """Calculates the first and last day of a given month string (YYYY-MM)."""
    try:
        year, month = map(int, selected_month_str.split('-'))
        first_day = date(year, month, 1)
        _, num_days = calendar.monthrange(year, month)
        last_day = date(year, month, num_days)
        return first_day, last_day
    except ValueError:
        app.logger.error(f"Invalid month format for monthly range: {selected_month_str}")
        return None, None

def get_date_range_for_yearly(selected_year_str):
    """Calculates the first and last day of a given year string (YYYY)."""
    try:
        year = int(selected_year_str)
        first_day = date(year, 1, 1)
        last_day = date(year, 12, 31)
        return first_day, last_day
    except ValueError:
        app.logger.error(f"Invalid year format for yearly range: {selected_year_str}")
        return None, None

# --- Manual Report Routes ---
@app.route('/reports/manual_request', methods=['GET'])
def manual_report_request_page():
    return render_template('manual_report_form.html')

@app.route('/reports/generate_custom', methods=['POST'])
def generate_custom_report():
    report_type = request.form.get('report_type')
    start_date_obj, end_date_obj = None, None
    report_title = "Custom Report"
    selected_date_for_template = None

    if report_type == 'daily':
        selected_date_str = request.form.get('selected_date_daily')
        start_date_obj, end_date_obj = get_date_range_for_daily(selected_date_str)
        if start_date_obj:
            report_title = f"Daily Report for {start_date_obj.strftime('%B %d, %Y')}"
            selected_date_for_template = start_date_obj 
    elif report_type == 'weekly':
        selected_date_str = request.form.get('selected_date_weekly')
        start_date_obj, end_date_obj = get_date_range_for_weekly(selected_date_str)
        if start_date_obj and end_date_obj:
            report_title = f"Weekly Report: {start_date_obj.strftime('%b %d, %Y')} to {end_date_obj.strftime('%b %d, %Y')}"
    elif report_type == 'monthly':
        selected_month_str = request.form.get('selected_month_monthly')
        start_date_obj, end_date_obj = get_date_range_for_monthly(selected_month_str)
        if start_date_obj:
            report_title = f"Monthly Report for {start_date_obj.strftime('%B %Y')}"
    elif report_type == 'yearly':
        selected_year_str = request.form.get('selected_year_yearly')
        start_date_obj, end_date_obj = get_date_range_for_yearly(selected_year_str)
        if start_date_obj:
            report_title = f"Yearly Report for {start_date_obj.strftime('%Y')}"
    else:
        flash('Invalid report type selected.', 'danger')
        return redirect(url_for('manual_report_request_page'))

    if not start_date_obj or (report_type != 'daily' and not end_date_obj):
        flash('Could not determine date range for the report. Please check your input.', 'danger')
        return redirect(url_for('manual_report_request_page'))

    expenditures = get_expenditures_for_week(start_date_obj, end_date_obj) # Re-use existing function
    maintenance_requests = get_maintenance_for_week(start_date_obj, end_date_obj) # Re-use
    cleaning_logs = get_cleaning_logs_for_week(start_date_obj, end_date_obj) # Re-use

    return render_template('weekly_report.html',
                           report_title=report_title,
                           expenditures=expenditures,
                           maintenance_requests=maintenance_requests,
                           cleaning_logs=cleaning_logs,
                           start_date=start_date_obj if report_type != 'daily' else None,
                           end_date=end_date_obj if report_type != 'daily' else None,
                           selected_date=selected_date_for_template)


# --- Facility Edit Route ---

@app.route('/facilities/delete', methods=['POST'])
def delete_facility():
    facility_id = request.form.get('facility_id')
    if not facility_id:
        flash('No facility specified for deletion.', 'danger')
        return redirect(url_for('manage_facilities_page'))
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("DELETE FROM facilities WHERE id=?", (facility_id,))
        db.commit()
        flash('Facility deleted successfully!', 'success')
    except Exception as e:
        db.rollback()
        flash(f'Error deleting facility: {e}', 'danger')
    return redirect(url_for('manage_facilities_page'))

@app.route('/facilities/edit/<int:facility_id>', methods=['GET', 'POST'])
def edit_facility(facility_id):
    db = get_db()
    cursor = db.cursor()
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        status = request.form.get('status')
        if not name or not description or not status:
            flash('All fields are required.', 'danger')
            return redirect(url_for('edit_facility', facility_id=facility_id))
        try:
            cursor.execute("""
                UPDATE facilities SET name=?, description=?, status=? WHERE id=?
            """, (name, description, status, facility_id))
            db.commit()
            flash('Facility updated successfully!', 'success')
            return redirect(url_for('manage_facilities_page'))
        except Exception as e:
            db.rollback()
            flash(f'Error updating facility: {e}', 'danger')
            return redirect(url_for('edit_facility', facility_id=facility_id))
    # GET
    cursor.execute("SELECT * FROM facilities WHERE id=?", (facility_id,))
    facility = cursor.fetchone()
    if not facility:
        flash('Facility not found.', 'danger')
        return redirect(url_for('manage_facilities_page'))
    facility_dict = dict(facility)
    return render_template('edit_facility.html', facility=facility_dict)

# --- Maintenance Request Edit Route ---
@app.route('/maintenance/edit/<int:request_id>', methods=['GET', 'POST'])
def edit_maintenance_request(request_id):
    db = get_db()
    cursor = db.cursor()
    if request.method == 'POST':
        issue_description = request.form.get('issue_description')
        priority = request.form.get('priority')
        status = request.form.get('status')
        if not issue_description or not priority or not status:
            flash('All fields are required.', 'danger')
            return redirect(url_for('edit_maintenance_request', request_id=request_id))
        try:
            cursor.execute("""
                UPDATE maintenance_requests SET description=?, priority=?, status=? WHERE id=?
            """, (issue_description, priority, status, request_id))
            db.commit()
            flash('Maintenance request updated successfully!', 'success')
            return redirect(url_for('maintenance_management_page'))
        except Exception as e:
            db.rollback()
            flash(f'Error updating maintenance request: {e}', 'danger')
            return redirect(url_for('edit_maintenance_request', request_id=request_id))
    # GET
    cursor.execute("""
        SELECT mr.id, f.name as facility_name, mr.description as issue_description, mr.priority, mr.status
        FROM maintenance_requests mr
        JOIN facilities f ON mr.facility_id = f.id
        WHERE mr.id=?
    """, (request_id,))
    req = cursor.fetchone()
    if not req:
        flash('Maintenance request not found.', 'danger')
        return redirect(url_for('maintenance_management_page'))
    req_dict = {
        'id': req[0],
        'facility_name': req[1],
        'issue_description': req[2],
        'priority': req[3],
        'status': req[4]
    }
    return render_template('edit_maintenance_request.html', request=req_dict)

# --- Maintenance Request Delete Route ---
@app.route('/maintenance/delete', methods=['POST'])
def delete_maintenance_request():
    request_id = request.form.get('request_id')
    if not request_id:
        flash('No maintenance request specified for deletion.', 'danger')
        return redirect(url_for('maintenance_management_page'))
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("DELETE FROM maintenance_requests WHERE id=?", (request_id,))
        db.commit()
        flash('Maintenance request deleted successfully!', 'success')
    except Exception as e:
        db.rollback()
        flash(f'Error deleting maintenance request: {e}', 'danger')
    return redirect(url_for('maintenance_management_page'))

# --- APScheduler Setup for Automated Weekly Reports ---
scheduler = BackgroundScheduler(daemon=True)

REPORTS_DIR = os.path.join(app.instance_path, 'generated_reports')
os.makedirs(REPORTS_DIR, exist_ok=True)

# Simple test job for debugging scheduler
def simple_test_job():
    with app.app_context():
        app.logger.info("APScheduler: simple_test_job started.")
        try:
            db = get_db()
            cursor = db.cursor()
            # Using a distinct file_path for simple_test_job to avoid potential UNIQUE constraint issues if 'test_path' was used before
            cursor.execute("INSERT INTO archived_reports (report_type, period_start_date, period_end_date, file_path, status, error_message) VALUES (?, ?, ?, ?, ?, ?)",
                           ('TEST', '2024-01-01', '2024-01-01', 'test_path_simple_job', 'test_fired', 'Simple job executed successfully'))
            db.commit()
            app.logger.info("APScheduler: simple_test_job successfully inserted dummy record into archived_reports.")
        except Exception as e:
            app.logger.error(f"APScheduler: simple_test_job failed: {e}", exc_info=True)
        finally:
            app.logger.info("APScheduler: simple_test_job finished.")


def generate_and_save_weekly_report():
    with app.app_context(): # Ensure we're in app context for db, render_template, mail
        app.logger.info("APScheduler: generate_and_save_weekly_report job ENTERED.")
        try:
            app.logger.info("APScheduler: Attempting to get DB for report generation.")
            db = get_db()
            app.logger.info("APScheduler: DB connection object obtained (or None if error). Attempting cursor.")
            cursor = db.cursor()
            app.logger.info("APScheduler: DB cursor obtained for report generation.")
            start_of_week, end_of_week = get_previous_week_dates()
            
            report_title = f"Automated Weekly Report: {start_of_week.strftime('%B %d, %Y')} to {end_of_week.strftime('%B %d, %Y')}"
            expenditures = get_expenditures_for_week(start_of_week, end_of_week)
            maintenance_requests = get_maintenance_for_week(start_of_week, end_of_week)
            cleaning_logs = get_cleaning_logs_for_week(start_of_week, end_of_week)

            # Render the report to an HTML string within a test request context
            with app.test_request_context():
                report_html_content = render_template('weekly_report.html', 
                                                report_title=report_title,
                                                expenditures=expenditures, 
                                                maintenance_requests=maintenance_requests, 
                                                cleaning_logs=cleaning_logs, 
                                                start_date=start_of_week, 
                                                end_date=end_of_week)
            
            # Save the report to a file
            file_name = f"Weekly_Report_{start_of_week.strftime('%Y-%m-%d')}_to_{end_of_week.strftime('%Y-%m-%d')}.html"
            file_path = os.path.join(REPORTS_DIR, file_name)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(report_html_content)
            app.logger.info(f"APScheduler: Successfully saved weekly report to {file_path}")

            # Log to archived_reports table
            cursor.execute("""
                INSERT INTO archived_reports (report_type, period_start_date, period_end_date, file_path, status)
                VALUES (?, ?, ?, ?, ?)
            """, ('weekly', start_of_week, end_of_week, file_path, 'success'))
            db.commit()
            app.logger.info(f"APScheduler: Logged generated report to archived_reports table.")

            # If report generation was successful, try to email it
            try:
                cursor.execute("SELECT email FROM report_recipients")
                recipients = [row[0] for row in cursor.fetchall()]
                if recipients:
                    app.logger.info(f"APScheduler: Found {len(recipients)} recipients for the weekly report.")
                    subject = f"Weekly Facility Report: {start_of_week.strftime('%Y-%m-%d')} - {end_of_week.strftime('%Y-%m-%d')}"
                    
                    # Send with HTML content as the body and also as an attachment
                    # Some email clients are better with one or the other.
                    msg = Message(subject,
                                  recipients=recipients,
                                  html=report_html_content) # HTML body
                    
                    # Add as attachment
                    msg.attach(filename=file_name,
                               content_type='text/html',
                               data=report_html_content.encode('utf-8'))
                    
                    mail.send(msg)
                    app.logger.info(f"APScheduler: Weekly report successfully emailed to {len(recipients)} recipients.")
                else:
                    app.logger.info("APScheduler: No recipients configured to email the weekly report.")
            except Exception as email_exc:
                app.logger.error(f"APScheduler: Failed to email weekly report. Error: {email_exc}", exc_info=True)
                # Optionally, update the archived_reports table to note email failure if critical
                # For now, just logging the error.

        except Exception as e:
            app.logger.error(f"APScheduler: Error during scheduled weekly report generation: {e}", exc_info=True)
            # Optionally, log failure to archived_reports table
            db = get_db()
            if db: # Check if db connection was established before error
                cursor = db.cursor()
                try:
                    cursor.execute("""
                        INSERT INTO archived_reports (report_type, period_start_date, period_end_date, file_path, status, error_message)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, ('weekly', 
                          start_of_week if 'start_of_week' in locals() else None, 
                          end_of_week if 'end_of_week' in locals() else None, 
                          file_path if 'file_path' in locals() else 'N/A_ERROR',
                          'failed', 
                          str(e)))
                    db.commit()
                    app.logger.info(f"APScheduler: Logged FAILED report generation to archived_reports table.")
                except Exception as db_err:
                    app.logger.error(f"APScheduler: Error logging failed report to DB: {db_err}", exc_info=True)
@app.route('/reports/archived')
def archived_reports_page():
    app.logger.info("Archived reports page accessed.")
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id, report_type, strftime('%Y-%m-%d %H:%M:%S', generated_at) as generated_at_formatted, period_start_date, period_end_date, file_path, status, error_message FROM archived_reports ORDER BY generated_at DESC")
    archived_reports = [dict(zip([column[0] for column in cursor.description], row)) for row in cursor.fetchall()]
    return render_template('archived_reports.html', reports=archived_reports)

@app.route('/reports/view/<int:report_id>')
def view_archived_report(report_id):
    app.logger.info(f"Attempting to view archived report ID: {report_id}")
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT file_path FROM archived_reports WHERE id = ?", (report_id,))
    report_record = cursor.fetchone()

    if report_record and report_record[0]:
        file_path = report_record[0]
        safe_base_dir = os.path.abspath(REPORTS_DIR)
        requested_file_abs_path = os.path.abspath(file_path)

        if requested_file_abs_path.startswith(safe_base_dir) and os.path.exists(requested_file_abs_path):
            try:
                return app.send_file(requested_file_abs_path, as_attachment=False)
            except Exception as send_file_e:
                app.logger.error(f"Error sending file {requested_file_abs_path} for report ID {report_id}: {send_file_e}", exc_info=True)
                flash(f'Error accessing report file: {send_file_e}', 'danger')
                return redirect(url_for('archived_reports_page'))
        else:
            app.logger.warning(f"Archived report file not found or path mismatch for ID {report_id}: {file_path}. Safe base: {safe_base_dir}, Requested: {requested_file_abs_path}")
            flash('Report file not found or access denied.', 'danger')
            return redirect(url_for('archived_reports_page'))
    else:
        app.logger.warning(f"Archived report record not found for ID {report_id}")
        flash('Archived report record not found.', 'danger')
        return redirect(url_for('archived_reports_page'))

@app.route('/reports/recipients', methods=['GET', 'POST'])
def manage_report_recipients_page():
    db = get_db()
    cursor = db.cursor()

    if request.method == 'POST':
        email_to_add = request.form.get('email_to_add')
        if email_to_add:
            try:
                cursor.execute("INSERT INTO report_recipients (email) VALUES (?)", (email_to_add,))
                db.commit()
                flash(f'Email {email_to_add} added to report recipients.', 'success')
            except sqlite3.IntegrityError: 
                flash(f'Email {email_to_add} is already in the recipient list.', 'warning')
            except Exception as e:
                flash(f'Error adding email: {e}', 'danger')
                app.logger.error(f"Error adding recipient email {email_to_add}: {e}", exc_info=True)
        return redirect(url_for('manage_report_recipients_page'))

    cursor.execute("SELECT id, email, strftime('%Y-%m-%d %H:%M:%S', added_at) as added_at_formatted FROM report_recipients ORDER BY email")
    recipients = [dict(zip([column[0] for column in cursor.description], row)) for row in cursor.fetchall()]
    return render_template('report_recipients.html', recipients=recipients)

@app.route('/reports/recipients/delete/<int:recipient_id>', methods=['POST'])
def delete_report_recipient(recipient_id):
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("DELETE FROM report_recipients WHERE id = ?", (recipient_id,))
        db.commit()
        flash('Recipient email deleted successfully.', 'success')
    except Exception as e:
        flash(f'Error deleting recipient: {e}', 'danger')
        app.logger.error(f"Error deleting recipient ID {recipient_id}: {e}", exc_info=True)
    return redirect(url_for('manage_report_recipients_page'))


@app.route('/cascade_test_route')
def cascade_test_route():
    return "Cascade test route is working!"

if __name__ == '__main__':
    app.logger.info("Initializing APScheduler in main block...")
    scheduler = BackgroundScheduler() # Removed daemon=True for this test

    # REPORTS_DIR is now defined globally and created at app startup.

    # Temporary trigger for testing simple_test_job (runs 3 minutes from app start)
    run_time = datetime.now() + timedelta(minutes=3)
    app.logger.info(f"APScheduler: Main block: Test trigger set for generate_and_save_weekly_report at {run_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    scheduler.add_job(
        func=generate_and_save_weekly_report, # Switched back to the actual report generator
        trigger='date',
        run_date=run_time,
        id='weekly_report_generator_test', # Changed ID to reflect the actual job
        name='Test: Generate and save weekly report once', # Changed name
        replace_existing=True
    )
    scheduler.start()
    app.logger.info("APScheduler: Main block: Scheduler started with generate_and_save_weekly_report scheduled.")

    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.logger.info("TEMPLATES_AUTO_RELOAD set to True")

    app.logger.info("Registered URL Rules:")
    for rule in app.url_map.iter_rules():
        app.logger.info(f"Endpoint: {rule.endpoint}, Methods: {list(rule.methods)}, Path: {str(rule)}")

    app.logger.info("Starting Flask development server with use_reloader=True.")
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=True)
