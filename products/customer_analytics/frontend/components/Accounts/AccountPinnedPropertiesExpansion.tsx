import { AccountPinnedPropertiesPanel } from '../../scenes/CustomerAnalyticsAccountScene/components/AccountPinnedPropertiesPanel'

export function AccountPinnedPropertiesExpansion({
    accountId,
    externalId,
}: {
    accountId: string
    externalId: string | null
}): JSX.Element {
    return (
        <div
            className="sticky left-0 w-[100cqw] max-w-full bg-bg-light"
            data-attr="account-pinned-properties-expansion"
        >
            <AccountPinnedPropertiesPanel
                accountId={accountId}
                externalId={externalId}
                layout="horizontal"
                source="list_expansion"
            />
        </div>
    )
}
