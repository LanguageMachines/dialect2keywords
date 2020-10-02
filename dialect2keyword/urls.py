"""dialect2keyword URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from main.views import home, upload, files, words, save, download

urlpatterns = [

    path('', home, name='home'),

    # Calls the upload function, given to the 'Upload' button on the home page.
    path('upload', upload, name='upload'),

    # Path to call 'files' views function, here 'folder_name' is a dynamic variable
    # that is given to the function
    path('files/<str:folder_name>', files, name='files'),

    # Path to call 'words' views function, here 'folder_name' and 'file_name' are a dynamic variables
    # that are given to the function
    path('words/<str:folder_name>/<str:file_name>/', words, name='words'),

    # Calls the save function, given to the 'Save Changes' button.
    path('words/<str:folder_name>/<str:file_name>/save/page=<int:page>', save, name='save'),

    # Calls the save function, given to the 'Download Current' button.
    path('words/<str:folder_name>/<str:file_name>/download', download, name='download'),
]
# Allows to serve the files under the media folder in the debug mode
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
