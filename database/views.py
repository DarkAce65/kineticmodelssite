from functools import lru_cache

import django_filters
from django.views.generic import TemplateView, DetailView, FormView, ListView
from django.urls import reverse

from .models import Species, Structure, SpeciesName, KineticModel


class IndexView(TemplateView):
    template_name = "index.html"


class ResourcesView(TemplateView):
    template_name = "resources.html"

    @staticmethod
    def parse_file_name(file_name):
        name = os.path.splitext(file_name)[0]
        parts = name.split("_")
        date = parts[0]
        date = date[0:4] + "-" + date[4:6] + "-" + date[6:]
        title = " ".join(parts[1:])
        title = title.replace("+", " and ")

        return (title, date, file_name)

    @property
    @lru_cache()
    def presentations(self):
        pres_list = []
        folder = os.path.join(settings.STATIC_ROOT, "presentations")
        if os.path.isdir(folder):
            for root, dirs, files in os.walk(folder):
                for file in files:
                    parsed = self.parse_file_name(file_name)
                    pres_list.append(parsed)

        return pres_list

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["presentations"] = self.presentations
        return context


class SpeciesFilter(django_filters.FilterSet):
    speciesname__name = django_filters.CharFilter(field_name="speciesname", lookup_expr="name", label="Species Name")
    isomer__inchi = django_filters.CharFilter(field_name="isomer", lookup_expr="inchi", label="Isomer InChI")
    isomer__structure__smiles = django_filters.CharFilter(field_name="isomer", lookup_expr="structure__smiles", label="Structure SMILES")
    isomer__structure__adjacencyList = django_filters.CharFilter(field_name="isomer", lookup_expr="structure__adjacencyList", label="Structure Adjacency List")
    isomer__structure__electronicState = django_filters.NumberFilter(field_name="isomer", lookup_expr="structure__electronicState", label="Structure Electronic State")
    
    class Meta:
        model = Species
        fields = ["sPrimeID", "formula", "inchi", "cas"]


class SpeciesDetail(DetailView):
    model = Species

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        structures = Structure.objects.filter(isomer__species=self.get_object())
        context["names"] = (
            self.get_object().speciesname_set.all().values_list("name", flat=True)
        )
        context["adjlists"] = structures.values_list("adjacencyList", flat=True)
        context["smiles"] = structures.values_list("smiles", flat=True)
        context["isomer_inchis"] = self.get_object().isomer_set.values_list(
            "inchi", flat=True
        )

        return context


# class Results(SingleObjectMixin, ListView):

#     def get(self, request, *args, **kwargs):
#         self.object = self.get_object(queryset=Species.objects.all())
#         return super().get(request, *args, **kwargs)

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context["species"] = self.object
#         return context

#     def get_queryset(self):
#         return self.object.kinetic_model_set.all()


# class TransportResults(Results):
#     template_name = "transport_results.html"


class ThermoResults(DetailView):
    template_name = "thermo_results.html"


class KineticModelDetail(DetailView):
    model = KineticModel


class ThermoDetail(KineticModelDetail):
    template_name = "thermo_detail.html"


class TransportDetail(KineticModelDetail):
    template_name = "transport_detail.html"


def kinetics_results(request):
    pass


def transport_result(request):
    pass


def thermo_result(request):
    pass


def kinetics_result(request):
    pass


def kinetics_search(request):
    pass


def reaction_results(request):
    pass


def solvation_search(request):
    pass
