# SPDX-License-Identifier: LGPL-3.0-only

"""Class ItemValidator for validation of Item objects."""

from doorstop import common, settings
from doorstop.common import DoorstopError, DoorstopInfo, DoorstopWarning
from doorstop.core.types import UID, Stamp

log = common.logger(__name__)


class ItemValidator:
    """Class for validation of Item objects."""

    def validate(self, item, skip=None, document_hook=None, item_hook=None):
        """Check the object for validity.

        :param item: item to validate
        :param skip: list of document prefixes to skip
        :param document_hook: function to call for custom document
            validation
        :param item_hook: function to call for custom item validation

        :return: indication that the object is valid

        """
        valid = True
        # Display all issues
        for issue in self.get_issues(
            item, skip=skip, document_hook=document_hook, item_hook=item_hook
        ):
            if isinstance(issue, DoorstopInfo) and not settings.WARN_ALL:
                log.info(issue)
            elif isinstance(issue, DoorstopWarning) and not settings.ERROR_ALL:
                log.warning(issue)
            else:
                assert isinstance(issue, DoorstopError)
                log.error(issue)
                valid = False
        # Return the result
        return valid

    def get_issues(
        self, item, skip=None, document_hook=None, item_hook=None
    ):  # pylint: disable=unused-argument
        """Yield all the item's issues.

        :param skip: list of document prefixes to skip

        :return: generator of :class:`~doorstop.common.DoorstopError`,
                              :class:`~doorstop.common.DoorstopWarning`,
                              :class:`~doorstop.common.DoorstopInfo`

        """
        assert document_hook is None
        assert item_hook is None
        skip = [] if skip is None else skip

        log.info("checking item %s...", item)

        # Verify the file can be parsed
        item.load()

        # Skip inactive items
        if not item.active:
            log.info("skipped inactive item: %s", item)
            return

        # Delay item save if reformatting
        if settings.REFORMAT:
            item.auto = False

        # Check text
        if not item.text:
            yield DoorstopWarning("no text")

        # Check external references
        if settings.CHECK_REF:
            try:
                item.find_ref()
            except DoorstopError as exc:
                yield exc

        # Check links
        if not item.normative and item.links:
            yield DoorstopWarning("non-normative, but has links")

        # Check links against the document
        yield from self._get_issues_document(item, item.document, skip)

        if item.tree:
            # Check links against the tree
            yield from self._get_issues_tree(item, item.tree)

            # Check links against both document and tree
            yield from self._get_issues_both(item, item.document, item.tree, skip)

        # Check review status
        if not item.reviewed:
            if settings.CHECK_REVIEW_STATUS:
                if not item.is_reviewed():
                    if settings.REVIEW_NEW_ITEMS:
                        item.review()
                    else:
                        yield DoorstopInfo("needs initial review")
                else:
                    yield DoorstopWarning("unreviewed changes")

        # Reformat the file
        if settings.REFORMAT:
            log.debug("reformatting item %s...", item)
            item.save()

    @staticmethod
    def _get_issues_document(item, document, skip):
        """Yield all the item's issues against its document."""
        log.debug("getting issues against document...")

        if document in skip:
            log.debug("skipping issues against document %s...", document)
            return

        # Verify an item's UID matches its document's prefix
        if item.uid.prefix != document.prefix:
            msg = "prefix differs from document ({})".format(document.prefix)
            yield DoorstopInfo(msg)

        # Verify that normative, non-derived items in a child document have at
        # least one link.  It is recommended that these items have an upward
        # link to an item in the parent document, however, this is not
        # enforced.  An info message is generated if this is not the case.
        if all((document.parent, item.normative, not item.derived)) and not item.links:
            msg = "no links to parent document: {}".format(document.parent)
            yield DoorstopWarning(msg)

        # Verify an item's links are to the correct parent
        for uid in item.links:
            try:
                prefix = uid.prefix
            except DoorstopError:
                msg = "invalid UID in links: {}".format(uid)
                yield DoorstopError(msg)
            else:
                if document.parent and prefix != document.parent:
                    # this is only 'info' because a document is allowed
                    # to contain items with a different prefix, but
                    # Doorstop will not create items like this
                    msg = "parent is '{}', but linked to: {}".format(
                        document.parent, uid
                    )
                    yield DoorstopInfo(msg)

    def _get_issues_tree(self, item, tree):
        """Yield all the item's issues against its tree."""
        log.debug("getting issues against tree...")

        # Verify an item's links are valid
        identifiers = set()
        for uid in item.links:
            try:
                parent = tree.find_item(uid)
            except DoorstopError:
                identifiers.add(uid)  # keep the invalid UID
                msg = "linked to unknown item: {}".format(uid)
                yield DoorstopError(msg)
            else:
                # check the parent item
                if not parent.active:
                    msg = "linked to inactive item: {}".format(parent)
                    yield DoorstopInfo(msg)
                if not parent.normative:
                    msg = "linked to non-normative item: {}".format(parent)
                    yield DoorstopWarning(msg)
                # check the link status
                if uid.stamp == Stamp(True):
                    uid.stamp = parent.stamp()
                elif not str(uid.stamp) and settings.STAMP_NEW_LINKS:
                    uid.stamp = parent.stamp()
                elif uid.stamp != parent.stamp():
                    if settings.CHECK_SUSPECT_LINKS:
                        msg = "suspect link: {}".format(parent)
                        yield DoorstopWarning(msg)
                # reformat the item's UID
                identifiers.add(UID(parent.uid, stamp=uid.stamp))

        # Apply the reformatted item UIDs
        if settings.REFORMAT:
            item.links = identifiers

    def _get_issues_both(self, item, document, tree, skip):
        """Yield all the item's issues against its document and tree."""
        log.debug("getting issues against document and tree...")

        if document.prefix in skip:
            log.debug("skipping issues against document %s...", document)
            return

        # Verify an item is being linked to (child links)
        if settings.CHECK_CHILD_LINKS and item.normative:
            find_all = settings.CHECK_CHILD_LINKS_STRICT or False
            items, documents = item.find_child_items_and_documents(
                document=document, tree=tree, find_all=find_all
            )

            if not items:
                for child_document in documents:
                    if document.prefix in skip:
                        msg = "skipping issues against document %s..."
                        log.debug(msg, child_document)
                        continue
                    msg = "no links from child document: {}".format(child_document)
                    yield DoorstopWarning(msg)
            elif settings.CHECK_CHILD_LINKS_STRICT:
                prefix = [item.prefix for item in items]
                for child in document.children:
                    if child in skip:
                        continue
                    if child not in prefix:
                        msg = 'no links from document: {}'.format(child)
                        yield DoorstopWarning(msg)
