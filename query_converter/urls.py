from django.urls import path
from .views import generate_sql_query,query_form, review_questions, approve_question, delete_question

urlpatterns = [
    path("generate_sql/", generate_sql_query, name="generate_sql"),
    path("query/", query_form, name="query_form"),
    path("review_questions/", review_questions, name="review_questions"),
    path("approve_question/", approve_question, name="approve_question"),
    path("delete_question/", delete_question, name="delete_question"),
]
