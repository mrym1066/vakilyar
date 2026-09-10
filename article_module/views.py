from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.views.generic import DetailView
from django.views.generic.list import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from article_module.models import Article, ArticleCategory


class ArticlesListView(LoginRequiredMixin, ListView):
    model = Article
    paginate_by = 4
    template_name = 'article_module/articles_page.html'
    login_url = '/login/'

    def get_context_data(self, *args, **kwargs):
        context = super(ArticlesListView, self).get_context_data(*args, **kwargs)
        return context

    def get_queryset(self):
        query = super(ArticlesListView, self).get_queryset()
        # is_active حذف شده از مدل (migration 0012)
        category_name = self.kwargs.get('category')
        if category_name is not None:
            query = query.filter(selected_categories__url_title__iexact=category_name)
        return query


class ArticleDetailView(LoginRequiredMixin, DetailView):
    model = Article
    template_name = 'article_module/article_detail_page.html'
    login_url = '/login/'

    def get_queryset(self):
        query = super(ArticleDetailView, self).get_queryset()
        # is_active حذف شده از مدل (migration 0012)
        return query

    def get_context_data(self, **kwargs):
        context = super(ArticleDetailView, self).get_context_data()
        article: Article = kwargs.get('object')
        return context


def article_categories_component(request: HttpRequest):
    article_main_categories = ArticleCategory.objects.prefetch_related('articlecategory_set')

    context = {
        'main_categories': article_main_categories
    }
    return render(request, 'article_module/components/article_categories_component.html', context)