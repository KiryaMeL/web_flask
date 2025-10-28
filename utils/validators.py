def validate_post_data(data):
    """
    Валидация данных для создания/обновления поста
    Возвращает tuple: (is_valid, errors)
    """
    errors = {}

    if not data:
        errors['general'] = 'No data provided'
        return False, errors

    # Проверка заголовка
    if 'title' not in data or not data.get('title'):
        errors['title'] = 'Title is required'
    elif len(data.get('title', '')) > 100:
        errors['title'] = 'Title must be less than 100 characters'

    # Проверка содержимого
    if 'content' not in data or not data.get('content'):
        errors['content'] = 'Content is required'

    return len(errors) == 0, errors



def validate_comment_data(data):
    """
    Валидация данных для создания комментария
    Возвращает tuple: (is_valid, errors)
    """
    errors = {}

    if not data:
        errors['general'] = 'No data provided'
        return False, errors

    # Проверка текста комментария
    if 'text' not in data or not data.get('text'):
        errors['text'] = 'Text is required'

    return len(errors) == 0, errors


def validate_user_data(data):
    """
    Валидация данных пользователя
    Возвращает tuple: (is_valid, errors)
    """
    errors = {}

    if not data:
        errors['general'] = 'No data provided'
        return False, errors

    if not data.get('username'):
        errors['username'] = 'Username is required'
    if not data.get('email'):
        errors['email'] = 'Email is required'
    if not data.get('password'):
        errors['password'] = 'Password is required'

    return len(errors) == 0, errors
