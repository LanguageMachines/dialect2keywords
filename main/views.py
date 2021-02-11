# -*- coding: utf-8 -*-

import os
from glob import glob
from multiprocessing import Process

from django.urls import reverse
from django.http import FileResponse
from django.shortcuts import render, redirect
from django.core.files import File
from django.core.files.storage import FileSystemStorage
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.conf import settings

from text_processing import process_file

def load_data(folder_name, file_name):
    """A helper class to load a "processed" file from the media folder

    .. warning:: This function never returns a "file not found error". Instead,
                 it returns an empty list if the file is not found at te path.

    Parameters
    ----------
    folder_name : string
        Works as the folder name

    file_name: string
        Name of the file without the file extension

    Returns
    -------
    data_ : list of list of strings
        Returns the data read from the file. Returns an empty list incase the file
        is not found.
    """
    data_ = []

    fs = FileSystemStorage()
    file_path = fs.path(folder_name + '/' + file_name + '.tsv')

    # Check whether the file exists, otherwise do nothing
    # In the template, we display a warning for missing file
    if os.path.isfile(file_path):

        # Read the processed data from the file system
        # Each line consists of a dialect word and the predicted keywords
        with open(file_path, 'r') as f:

            for i, line in enumerate(f.readlines()):
                if i == 0:
                    continue
                # The original processed file contains confidence scores within paranthesis
                # For easier reading on the templating, we change the structure into
                # [dialect, keyword1, confidence1, keyword2, confidence2]
                line = line.strip().replace(' (', '|').replace(')', '')
                line = [ls for l in line.split('\t') for ls in l.split('|') if ls]
                data_.append(line)

    return data_

def home(request):
    """Loads the Home page
    """
    return render(request, 'home.html', {})

def upload(request):
    """File upload code that runs when the 'Upload' button is clicked
    """
    # The files are uploaded in a form,
    # and so, we capture the action as a POST request here
    if request.method == 'POST':

        # Read the posted values
        upfile = request.FILES['upfile'] # file object
        folder_name = request.POST['folder_name'] # string
        email_address = request.POST.get('email-address', '') # string, (default='')

        # Next lines saves the uploaded file into the project's 'media' folder
        # Notice that we save the file in a nested folder named as the give 'folder_name'
        fs = FileSystemStorage()
        file_name = fs.save(folder_name + '/' + upfile.name, upfile)
        file_name = file_name.split('.txt')[0]
        # Data URL is shown back on the webpage after the successful upload
        data_url = 'https://dialect2keyword.cls.ru.nl/words/' + file_name + '_processed/'

        # Here we call the function that will process the uploaded data_
        # We use parallel processing to be able to load the next page
        # without waiting for the processing to be completed
        p = Process(target=process_file, args=(file_name, email_address))
        p.start()

    else:
        folder_name = False
        data_url = False

    return render(request, 'upload.html', {
        'folder_name': folder_name, # string or bool
        'data_url' : data_url, # string or bool
    })

def words(request, folder_name, file_name):
    """Reads the processed data from the file system and sends it to the front end
    """
    # The page number for the paginator
    page = request.GET.get('page', 1) # integer, (default=1)
    page_range = []

    # Load the requested data from the file
    data_ = load_data(folder_name, file_name)

    if data_:
        # We cannot display files with large number of words at once
        # Thus, we use a pagination system
        paginator = Paginator(data_, settings.MAX_WORDS_PAGE)

        try:
            data_ = paginator.page(page)
        except (PageNotAnInteger, InvalidPage):
            data_ = paginator.page(1)
        except EmptyPage:
            data_ = paginator.page(paginator.num_pages)

        # The list of previous user input
        # These are given to input objects via javascript for a continuous
        prev_user_input = '|'.join([w[5] if len(w) == 6 else '' for w in data_])

        # Shorten the list of displayed number of pages
        index = data_.number - 1
        max_index = len(paginator.page_range)
        start_index = index - 7 if index >= 7 else 0
        end_index = index + 7 if index <= max_index - 7 else max_index
        page_range = list(paginator.page_range)[start_index:end_index]


    return render(request, 'words.html', {
        'words' : data_, # paginator object
        'prev_user_input': prev_user_input, # strings
        'folder_name': folder_name, # string
        'file_name': file_name, # string
        'page_range': page_range,
        'page': page, # integer
    })

def save(request, folder_name, file_name, page):
    """Saves the user input into the processed files back
    """
    if request.method == 'POST':

        # Read the input that the user filled and submitted via words.html
        # This creates a list of dictionaries where the dialect words are
        # the keys and the user inputs are the values.
        user_input = [{key.split('input-for-')[1]: val}
                      for key, val in request.POST.items()
                      if key.startswith('input-for-')]

        # Load the entire dataset from the file
        data_ = load_data(folder_name, file_name)

        # As user only given input on a specific page, we can align the user inputs
        # and the original data by only looping over the paginated subset of the dataset
        for i, item in enumerate(data_[(page-1)*settings.MAX_WORDS_PAGE:page*settings.MAX_WORDS_PAGE]):
            # For the sake of mind, the if statement here checks whether
            # the original data and the user input actually aligned
            # by checking whether the dialect word in the data is in the user input
            if item[0] in user_input[i]:
                if len(item) == 6:
                    # If there is already aprevious user input,
                    # just replace the previous one
                    item[5] = user_input[i][item[0]]
                elif len(item) == 5:
                    # Add the user input to the data. Each item here becomes:
                    # [dialect_word, first_estimate, first_estimate_confidence,
                    # second_estimate, second_estimate_confidence, user_input]
                    item.append(user_input[i][item[0]])

        # Prepare the string to be written to the file
        to_write = 'Dialect Word\tFirst Estimate\tSecond Estimate\tManual Annotation\n'
        for item in data_:
            to_write += item[0] + '\t'
            to_write += item[1] + ' (' + str(item[2]) + ')' + '\t'
            to_write += item[3] + ' (' + str(item[4]) + ')' + '\t'
            to_write += (item[5] if len(item) == 6 else '') + '\t'
            to_write += '\n'

        # Write to the file
        with open(settings.MEDIA_ROOT + '/' + folder_name  + '/' + file_name + '.tsv', 'w') as fn:
            myfile = File(fn)
            myfile.write(to_write)

    # Redirect back to the same page
    return redirect('/words/' + folder_name + '/' + file_name  + '/?page=' + str(page))

def download(request, folder_name, file_name):
    """Function to download files from the media folder
    """
    fs = FileSystemStorage()
    response = FileResponse(fs.open(folder_name + '/' + file_name + '.tsv', 'rb'), content_type='application/force-download')
    response['Content-Disposition'] = 'attachment; filename="' + file_name + '.tsv"'

    return response

def files(request, folder_name):
    """Retrieves the processed file names previously uploaded under the same folder_name
    """
    # Read the file names from the folder of the user
    # Returns a list of file names without the file extensions
    file_names = [os.path.splitext(os.path.basename(file_path))[0]
                  for file_path in glob(settings.MEDIA_ROOT + '/' + folder_name + '/*')
                  if '_processed' in file_path]

    return render(request, 'files.html', {
        'folder_name': folder_name, # string
        'file_names': file_names, # string
    })
