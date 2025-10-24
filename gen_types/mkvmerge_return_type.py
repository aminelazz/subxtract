from typing import Literal, TypedDict, Union
from typing_extensions import Required


class MkvmergeIdentificationOutput(TypedDict, total=False):
    """
    mkvmerge identification output.

    The JSON output produced by mkvmerge's file identification mode

    id: https://mkvtoolnix.download/doc/mkvmerge-identification-output-schema-v20.json
    """

    attachments: list["_MkvmergeIdentificationOutputAttachmentsItem"]
    """ an array describing the attachments found if any """

    chapters: list["_MkvmergeIdentificationOutputChaptersItem"]
    container: "_MkvmergeIdentificationOutputContainer"
    """ information about the identified container """

    errors: list[str]
    file_name: str
    """
    the identified file's name

    minLength: 1
    """

    global_tags: list["_MkvmergeIdentificationOutputGlobalTagsItem"]
    identification_format_version: int
    """
    The output format's version

    minimum: 20
    maximum: 20
    """

    track_tags: list["_MkvmergeIdentificationOutputTrackTagsItem"]
    tracks: list["_MkvmergeIdentificationOutputTracksItem"]
    warnings: list[str]


class _MkvmergeIdentificationOutputAttachmentsItem(TypedDict, total=False):
    content_type: str
    """ minLength: 1 """

    description: str
    file_name: Required[str]
    """ Required property """

    id: Required[int]
    """
    minimum: 0

    Required property
    """

    size: Required[int]
    """
    minimum: 0

    Required property
    """

    properties: Required["_MkvmergeIdentificationOutputAttachmentsItemProperties"]
    """ Required property """

    type: str


class _MkvmergeIdentificationOutputAttachmentsItemProperties(TypedDict, total=False):
    uid: int
    """ minimum: 0 """



class _MkvmergeIdentificationOutputChaptersItem(TypedDict, total=False):
    num_entries: Required[int]
    """ Required property """



class _MkvmergeIdentificationOutputContainer(TypedDict, total=False):
    """ information about the identified container """

    properties: "_MkvmergeIdentificationOutputContainerProperties"
    """ additional properties for the container varying by container format """

    recognized: Required[bool]
    """
    States whether or not mkvmerge knows about the format

    Required property
    """

    supported: Required[bool]
    """
    States whether or not mkvmerge can read the format

    Required property
    """

    type: str
    """
    A human-readable description/name for the container format

    minLength: 1
    """



class _MkvmergeIdentificationOutputContainerProperties(TypedDict, total=False):
    """ additional properties for the container varying by container format """

    container_type: int
    """
    A unique number identifying the container type that's supposed to stay constant over all future releases of MKVToolNix

    minLength: 1
    """

    date_local: str
    """
    The muxing date in ISO 8601 format (in local time zone)

    pattern: ^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}([+-][0-9]{2}:[0-9]{2}|Z)$
    """

    date_utc: str
    """
    The muxing date in ISO 8601 format (in UTC)

    pattern: ^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}([+-][0-9]{2}:[0-9]{2}|Z)$
    """

    duration: int
    """
    The file's/segment's duration in nanoseconds

    minimum: 0
    """

    is_providing_timestamps: bool
    """ States whether or not the container has timestamps for the packets (e.g. Matroska, MP4) or not (e.g. SRT, MP3) """

    muxing_application: str
    """ A Unicode string containing the name and possibly version of the low-level library or application that created the file """

    next_segment_uid: str
    """
    A hexadecimal string of the next segment's UID (only for Matroska files)

    minLength: 32
    maxLength: 32
    """

    other_file: list[str]
    """ An array of names of additional files processed as well """

    playlist: bool
    """ States whether or not the identified file is a playlist (e.g. MPLS) referring to several other files """

    playlist_chapters: int
    """
    The number of chapters in a playlist if it is a one

    minimum: 0
    """

    playlist_duration: int
    """
    The total duration in nanoseconds of all files referenced by the playlist if it is a one

    minimum: 0
    """

    playlist_file: list[str]
    """ An array of file names the playlist contains """

    playlist_size: int
    """
    The total size in bytes of all files referenced by the playlist if it is a one

    minimum: 0
    """

    previous_segment_uid: str
    """
    A hexadecimal string of the previous segment's UID (only for Matroska files)

    minLength: 32
    maxLength: 32
    """

    programs: list["_MkvmergeIdentificationOutputContainerPropertiesProgramsItem"]
    """ A container describing multiple programs multiplexed into the source file, e.g. multiple programs in one DVB transport stream """

    segment_uid: str
    """
    A hexadecimal string of the segment's UID (only for Matroska files)

    minLength: 32
    maxLength: 32
    """

    timestamp_scale: int
    """
    Base unit for segment ticks and track ticks, in nanoseconds. A timestamp_scale value of 1.000.000 means scaled timestamps in the segment are expressed in milliseconds.

    minimum: 0
    """

    title: str
    writing_application: str
    """ A Unicode string containing the name and possibly version of the high-level application that created the file """



class _MkvmergeIdentificationOutputContainerPropertiesProgramsItem(TypedDict, total=False):
    """ Properties describing a single program """

    program_number: int
    """
    A unique number identifying a set of tracks that belong together; used e.g. in DVB for multiplexing multiple stations within a single transport stream

    minimum: 0
    """

    service_name: str
    """ The name of a service provided by this program, e.g. a TV channel name such as 'arte HD' """

    service_provider: str
    """ The name of the provider of the service provided by this program, e.g. a TV station name such as 'ARD' """



class _MkvmergeIdentificationOutputGlobalTagsItem(TypedDict, total=False):
    num_entries: Required[int]
    """ Required property """



class _MkvmergeIdentificationOutputTrackTagsItem(TypedDict, total=False):
    num_entries: Required[int]
    """ Required property """

    track_id: Required[int]
    """ Required property """



class _MkvmergeIdentificationOutputTracksItem(TypedDict, total=False):
    codec: Required[str]
    """
    minLength: 1

    Required property
    """

    id: Required[int]
    """
    minLength: 0

    Required property
    """

    type: Required[str]
    """ Required property """

    properties: Union[dict[str, str], "_MkvmergeIdentificationOutputTracksItemPropertiesTyped"]
    """

    WARNING: Normally the types should be a mix of each other instead of Union.
    See: https://github.com/camptocamp/jsonschema-gentypes/issues/7
    """



_MkvmergeIdentificationOutputTracksItemPropertiesAacIsSbr = Literal['true'] | Literal['false'] | Literal['unknown']
_MKVMERGEIDENTIFICATIONOUTPUTTRACKSITEMPROPERTIESAACISSBR_TRUE: Literal['true'] = "true"
"""The values for the '_MkvmergeIdentificationOutputTracksItemPropertiesAacIsSbr' enum"""
_MKVMERGEIDENTIFICATIONOUTPUTTRACKSITEMPROPERTIESAACISSBR_FALSE: Literal['false'] = "false"
"""The values for the '_MkvmergeIdentificationOutputTracksItemPropertiesAacIsSbr' enum"""
_MKVMERGEIDENTIFICATIONOUTPUTTRACKSITEMPROPERTIESAACISSBR_UNKNOWN: Literal['unknown'] = "unknown"
"""The values for the '_MkvmergeIdentificationOutputTracksItemPropertiesAacIsSbr' enum"""



_MkvmergeIdentificationOutputTracksItemPropertiesMultiplexedTracksItem = int
""" minimum: 0 """



class _MkvmergeIdentificationOutputTracksItemPropertiesTyped(TypedDict, total=False):
    aac_is_sbr: "_MkvmergeIdentificationOutputTracksItemPropertiesAacIsSbr"
    alpha_mode: int
    """
    minimum: 0
    maximum: 1
    """

    audio_bits_per_sample: int
    """ minimum: 0 """

    audio_channels: int
    """ minimum: 0 """

    audio_emphasis: int
    """
    Audio emphasis applied on audio samples. The player MUST apply the inverse emphasis to get the proper audio samples.

    minimum: 0
    """

    audio_sampling_frequency: int
    """ minimum: 0 """

    cb_subsample: str
    """ pattern: ^-?[0-9]+,-?[0-9]+$ """

    chroma_siting: str
    """ pattern: ^-?[0-9]+,-?[0-9]+$ """

    chroma_subsample: str
    """ pattern: ^-?[0-9]+,-?[0-9]+$ """

    chromaticity_coordinates: str
    """ pattern: ^-?[0-9]+(\.[0-9]+)?,-?[0-9]+(\.[0-9]+)?,-?[0-9]+(\.[0-9]+)?,-?[0-9]+(\.[0-9]+)?,-?[0-9]+(\.[0-9]+)?,-?[0-9]+(\.[0-9]+)?$ """

    codec_delay: int
    codec_id: str
    codec_name: str
    codec_private_data: str
    codec_private_length: int
    """ minimum: 0 """

    content_encoding_algorithms: str
    """ minLength: 1 """

    color_bits_per_channel: int
    color_matrix_coefficients: int
    color_primaries: int
    color_range: int
    color_transfer_characteristics: int
    default_duration: int
    """ minimum: 0 """

    default_track: bool
    display_dimensions: str
    """ pattern: ^[0-9]+x[0-9]+$ """

    display_unit: int
    """ minimum: 0 """

    enabled_track: bool
    encoding: str
    """ The encoding/character set of a track containing text (e.g. subtitles) if it can be determined with confidence. For such tracks the encoding cannot be changed by the user. """

    forced_track: bool
    flag_hearing_impaired: bool
    """ Can be set if that track is suitable for users with hearing impairments. """

    flag_visual_impaired: bool
    """ Can be set if that track is suitable for users with visual impairments. """

    flag_text_descriptions: bool
    """ Can be set if that track contains textual descriptions of video content suitable for playback via a text-to-speech system for a visually-impaired user. """

    flag_original: bool
    """ Can be set if that track is in the content's original language (not a translation). """

    flag_commentary: bool
    """ Can be set if that track contains commentary. """

    language: str
    """ The track's language as an ISO 639-2 language code """

    language_ietf: str
    """ The track's language as an IETF BCP 47/RFC 5646 language tag """

    max_content_light: int
    max_frame_light: int
    max_luminance: int | float
    min_luminance: int | float
    minimum_timestamp: int
    """
    The minimum timestamp in nanoseconds of all the frames of this track found within the first couple of seconds of the file

    minimum: 0
    """

    multiplexed_tracks: list["_MkvmergeIdentificationOutputTracksItemPropertiesMultiplexedTracksItem"]
    """ An array of track IDs indicating which tracks were originally multiplexed within the same track in the source file """

    number: int
    """ minimum: 0 """

    num_index_entries: int
    """ minimum: 0 """

    packetizer: str
    """ minLength: 1 """

    pixel_dimensions: str
    """ pattern: ^[0-9]+x[0-9]+$ """

    program_number: int
    """
    A unique number identifying a set of tracks that belong together; used e.g. in DVB for multiplexing multiple stations within a single transport stream

    minimum: 0
    """

    projection_pose_pitch: int | float
    projection_pose_roll: int | float
    projection_pose_yaw: int | float
    projection_private: str
    """ pattern: ^([0-9A-F]{2})*$ """

    projection_type: int
    stereo_mode: int
    """ minimum: 0 """

    stream_id: int
    """
    A format-specific ID identifying a track, possibly in combination with a 'sub_stream_id' (e.g. the program ID in an MPEG transport stream)

    minimum: 0
    """

    sub_stream_id: int
    """
    A format-specific ID identifying a track together with a 'stream_id'

    minimum: 0
    """

    teletext_page: int
    """ minimum: 0 """

    text_subtitles: bool
    track_name: str
    uid: int
    """ minimum: 0 """

    white_color_coordinates: str
    """ pattern: ^-?[0-9]+(\.[0-9]+)?,-?[0-9]+(\.[0-9]+)?$ """

