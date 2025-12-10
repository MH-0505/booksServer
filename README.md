# Backend aplikacji Books

## Wymagania
*   Python (3.13)
*   pip (>= 24)

## Uruchomienie

1.  Uruchom terminal w katalogu `\booksServer`

2.  Utwórz i aktywuj wirtualne środowisko:
    ```bash
    python -m venv venv
    source venv/bin/activate  # macOS/Linux
    .\venv\Scripts\activate   # Windows
    ```

3.  Zainstaluj zależności:
    ```bash
    pip install -r requirements.txt
    ```

4.  Skonfiguruj zmienne środowiskowe w pliku `\booksServer\.env` według wzoru:
    ```txt
    DJANGO_SECRET=django-insecure--i!itsp&uf-g^p)4926qzz5-@+21)hhqif%p-gb9m2say2r-3f
    DEBUG=True
    ALLOWED_HOSTS=localhost,127.0.0.1
    
    # baza danych, można użyć poniższych zmiennych lub analogicznie skonfigurować swoją bazę danych 
    DATABASE_URL=postgresql://postgres.jfjvwsnouwdadynxodwv:***REMOVED***@aws-1-eu-central-1.pooler.supabase.com:5432/postgres
    SUPABASE_URL=https://jfjvwsnouwdadynxodwv.supabase.co
    SUPABASE_KEY=<prywatny klucz supabase>    # można zostawić puste, wymagane tylko do przesyłania obrazów do bazy
    SUPABASE_COVERS_BUCKET=covers
    SUPABASE_AVATAR_BUCKET=avatars
    ```

5.  Wykonaj, jeśli korzystasz z nowej bazy danych:
    ```bash
    python manage.py migrate
    python manage.py createsuperuser
    ```

6.  Uruchom serwer deweloperski:
    ```bash
    python manage.py runserver
    ```