# Demo constants
REVIEWING = 'reviewing'
REJECTED = 'rejected'
APPROVED = 'approved'
OPEN = 'open'
CLOSED = 'closed'
ABORTED = 'aborted'
CREATED = 'created'
COMMENT = 'comment'
UPDATED = 'updated'
REOPENED = 'reopened'
DRAFT = 'draft'
CANCELLED = 'cancelled'

# Attachment Constants
IMAGE = 'image'
DOCUMENT = 'document'
MOVIE = 'movie'
AUDIO = 'audio'
OTHER = 'other'

ATTACHMENT_MAP = {
    IMAGE: [
        'png', 'gif', 'bmp', 'jpg', 'jpeg', 'tiff', 'svg',
    ],
    DOCUMENT: [
        'doc', 'pdf', 'docx', 'txt', 'xls', 'xlsx', 'xlsm', 'pptx', 'ppt',
        'pptm', 'xlt',
    ],
    MOVIE: [
        'mkv', 'mov', 'avi', 'divx', 'mpeg', 'webm', 'mp4', 'mpeg4'
    ],
    AUDIO: [
        'mp3', 'wav', 'aiff', 'ogg', 'mpeg3'
    ],
}
