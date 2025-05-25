@app.route('/update/<int:id>', methods=['GET', 'POST'])
@login_required
def update(id):
    task = Todo.query.get_or_404(id)
    
    # Check authorization
    if not (current_user.id == task.author_id or current_user.is_admin):
        flash('You are not authorized to edit this challenge')
        return redirect(url_for('forum'))

    if request.method == 'GET':
        return render_template('update.html', task=task)

    if request.method == 'POST':
        print(f"Updating task {id} by user {current_user.username}")  # Debug log
        task.title = request.form.get('title')
        task.main_question = request.form.get('mainQuestion')
        task.sub_questions = request.form.get('subQuestions')
        task.description = request.form.get('description')
        task.end_product = request.form.get('endProduct')
        task.category = request.form.get('categorie')
        # Note: name field is not updated - it stays as original author's username
        
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                task.image = filename
        
        try:
            db.session.commit()
            flash('Challenge updated successfully')
            return redirect(url_for('forum'))
        except Exception as e:
            print(f"Error updating challenge: {str(e)}")  # Debug logging
            db.session.rollback()
            flash('There was an issue updating your challenge')
            return redirect(url_for('forum'))
