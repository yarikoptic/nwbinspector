"""Check functions that examine general NWBFile metadata."""
import re
from datetime import datetime
from warnings import warn

from pynwb import NWBFile, ProcessingModule
from pynwb.file import Subject

from ..register_checks import register_check, InspectorMessage, Importance
from ..utils import is_module_installed

duration_regex = (
    r"^P(?!$)(\d+(?:\.\d+)?Y)?(\d+(?:\.\d+)?M)?(\d+(?:\.\d+)?W)?(\d+(?:\.\d+)?D)?(T(?=\d)(\d+(?:\.\d+)?H)?(\d+(?:\.\d+)"
    r"?M)?(\d+(?:\.\d+)?S)?)?$"
)
species_regex = r"[A-Z][a-z]* [a-z]+"

PROCESSING_MODULE_CONFIG = ["ophys", "ecephys", "icephys", "behavior", "misc", "ogen", "retinotopy"]


@register_check(importance=Importance.BEST_PRACTICE_SUGGESTION, neurodata_type=NWBFile)
def check_session_start_time_old_date(nwbfile: NWBFile):
    """Check if the session_start_time was set to an appropriate value."""
    if nwbfile.session_start_time <= datetime(1980, 1, 1).astimezone():
        return InspectorMessage(
            message=(
                f"The session_start_time ({nwbfile.session_start_time}) may not be set to the true date of the "
                "recording."
            )
        )


@register_check(importance=Importance.CRITICAL, neurodata_type=NWBFile)
def check_session_start_time_future_date(nwbfile: NWBFile):
    """Check if the session_start_time was set to an appropriate value."""
    if nwbfile.session_start_time >= datetime.now().astimezone():
        return InspectorMessage(
            message=f"The session_start_time ({nwbfile.session_start_time}) is set to a future date and time."
        )


@register_check(importance=Importance.BEST_PRACTICE_SUGGESTION, neurodata_type=NWBFile)
def check_experimenter_exists(nwbfile: NWBFile):
    """Check if an experimenter has been added for the session."""
    if not nwbfile.experimenter:
        return InspectorMessage(message="Experimenter is missing.")


@register_check(importance=Importance.BEST_PRACTICE_SUGGESTION, neurodata_type=NWBFile)
def check_experimenter_form(nwbfile: NWBFile):
    """Check the text form of each experimenter to see if it matches the DANDI regex pattern."""
    if not is_module_installed(module_name="dandi"):
        warn(
            "It is strongly recommended to download DANDI alongside the NWB Inspector \n\n"
            "\tpip install dandi\n\nor\n\n\tpip install nwbinspector.[dandi]\n"
        )
        return

    from dandischema.models import NAME_PATTERN

    for experimenter in nwbfile.experimenter:
        experimenter = experimenter.decode() if isinstance(experimenter, bytes) else experimenter
        if re.match(string=experimenter, pattern=NAME_PATTERN) is None:
            yield InspectorMessage(
                message=(
                    f"The name of experimenter '{experimenter}' does not match the DANDI form "
                    "(Last, First Middle or Last, First M.)."
                )
            )


@register_check(importance=Importance.BEST_PRACTICE_SUGGESTION, neurodata_type=NWBFile)
def check_experiment_description(nwbfile: NWBFile):
    """Check if a description has been added for the session."""
    if not nwbfile.experiment_description:
        return InspectorMessage(message="Experiment description is missing.")


@register_check(importance=Importance.BEST_PRACTICE_SUGGESTION, neurodata_type=NWBFile)
def check_institution(nwbfile: NWBFile):
    """Check if a description has been added for the session."""
    if not nwbfile.institution:
        return InspectorMessage(message="Metadata /general/institution is missing.")


@register_check(importance=Importance.BEST_PRACTICE_SUGGESTION, neurodata_type=NWBFile)
def check_keywords(nwbfile: NWBFile):
    """Check if keywords have been added for the session."""
    if not nwbfile.keywords:
        return InspectorMessage(message="Metadata /general/keywords is missing.")


@register_check(importance=Importance.BEST_PRACTICE_SUGGESTION, neurodata_type=NWBFile)
def check_subject_exists(nwbfile: NWBFile):
    """Check if subject exists."""
    if nwbfile.subject is None:
        return InspectorMessage(message="Subject is missing.")


@register_check(importance=Importance.BEST_PRACTICE_SUGGESTION, neurodata_type=NWBFile)
def check_doi_publications(nwbfile: NWBFile):
    """Check if related_publications has been properly added as 'doi: ###' or an external 'doi' link."""
    valid_starts = ["doi:", "http://dx.doi.org/", "https://doi.org/"]

    if not nwbfile.related_publications:
        return
    for publication in nwbfile.related_publications:
        publication = publication.decode() if isinstance(publication, bytes) else publication
        if not any((publication.startswith(valid_start) for valid_start in valid_starts)):
            yield InspectorMessage(
                message=(
                    f"Metadata /general/related_publications '{publication}' does not start with 'doi: ###' and is "
                    "not an external 'doi' link."
                )
            )


@register_check(importance=Importance.BEST_PRACTICE_SUGGESTION, neurodata_type=Subject)
def check_subject_age(subject: Subject):
    """Check if the Subject age is in ISO 8601."""
    if subject.age is None:
        if subject.date_of_birth is None:
            return InspectorMessage(message="Subject is missing age and date_of_birth.")
    elif not re.fullmatch(duration_regex, subject.age):
        return InspectorMessage(
            message=(
                f"Subject age, '{subject.age}', does not follow ISO 8601 duration format, e.g. 'P2Y' for 2 years "
                "or 'P23W' for 23 weeks."
            )
        )


@register_check(importance=Importance.BEST_PRACTICE_SUGGESTION, neurodata_type=Subject)
def check_subject_id_exists(subject: Subject):
    """Check if subject_id is defined."""
    if subject.subject_id is None:
        return InspectorMessage(message="subject_id is missing.")


@register_check(importance=Importance.BEST_PRACTICE_SUGGESTION, neurodata_type=Subject)
def check_subject_sex(subject: Subject):
    """Check if the subject sex has been specified, if one exists."""
    if subject and not subject.sex:
        return InspectorMessage(message="Subject.sex is missing.")
    elif subject.sex not in ("M", "F", "O", "U"):
        return InspectorMessage(
            message="Subject.sex should be one of: 'M' (male), 'F' (female), 'O' (other), or 'U' (unknown)."
        )


@register_check(importance=Importance.BEST_PRACTICE_VIOLATION, neurodata_type=Subject)
def check_subject_species_exists(subject: Subject):
    """Check if the subject species has been specified."""
    if not subject.species:
        return InspectorMessage(message="Subject species is missing.")


@register_check(importance=Importance.BEST_PRACTICE_VIOLATION, neurodata_type=Subject)
def check_subject_species_latin_binomial(subject: Subject):
    """Check if the subject species follows latin binomial form."""
    if subject.species and not re.fullmatch(species_regex, subject.species):
        return InspectorMessage(
            message=(
                f"Subject species '{subject.species}' should be in latin binomial form, e.g. 'Mus musculus' and "
                "'Homo sapiens'"
            ),
        )


@register_check(importance=Importance.BEST_PRACTICE_SUGGESTION, neurodata_type=ProcessingModule)
def check_processing_module_name(processing_module: ProcessingModule):
    """Check if the name of a processing module is of a valid modality."""
    if processing_module.name not in PROCESSING_MODULE_CONFIG:
        return InspectorMessage(
            message=(
                f"Processing module is named {processing_module.name}. It is recommended to use the "
                f"schema module names: {', '.join(PROCESSING_MODULE_CONFIG)}"
            )
        )
