from django.http import JsonResponse, HttpResponse

# Tests
def test(request):
    return JsonResponse(dict(message ='connection established'))