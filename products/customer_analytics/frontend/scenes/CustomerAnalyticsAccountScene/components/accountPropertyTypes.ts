import type {
    AccountRelationshipDefinitionApi,
    CustomPropertyDefinitionApi,
} from 'products/customer_analytics/frontend/generated/api.schemas'

export const MAX_PINNED_ACCOUNT_PROPERTIES = 50

export type AccountCustomPropertyValue = string | number | boolean | null

export type AccountCustomPropertyProvenance = 'manual' | 'workflow' | 'warehouse' | 'canonical'

export interface AccountRelationshipMember {
    id: number
    email: string
    name?: string
}

export interface AccountCustomProperty {
    key: string
    kind: 'custom'
    definition: CustomPropertyDefinitionApi
    value: AccountCustomPropertyValue
    provenance: AccountCustomPropertyProvenance
    editable?: boolean
}

export interface AccountRelationshipProperty {
    key: string
    kind: 'relationship'
    definition: AccountRelationshipDefinitionApi
    members: AccountRelationshipMember[]
    editable?: boolean
}

export type AccountFieldId = 'external_id'

export interface AccountFieldDefinition {
    id: AccountFieldId
    name: string
    // Mid-sentence form for the "Copied ... to clipboard" toast.
    copyDescription: string
}

export const PINNABLE_ACCOUNT_FIELDS: AccountFieldDefinition[] = [
    { id: 'external_id', name: 'External ID', copyDescription: 'external ID' },
]

export type AccountFieldValues = Record<AccountFieldId, string | null>

export interface AccountFieldProperty {
    key: string
    kind: 'account_field'
    definition: AccountFieldDefinition
    value: string | null
    editable: false
}

export type AccountSidebarProperty = AccountCustomProperty | AccountRelationshipProperty | AccountFieldProperty

export const ACCOUNT_PROPERTY_KIND_LABELS: Record<AccountSidebarProperty['kind'], string> = {
    custom: 'Custom property',
    relationship: 'Relationship',
    account_field: 'Account property',
}

export interface AccountPropertyOption {
    key: string
    label: string
    kind: AccountSidebarProperty['kind']
}

export function isCustomPropertyEditable(provenance: AccountCustomPropertyProvenance): boolean {
    return provenance === 'manual' || provenance === 'workflow'
}

export function isSidebarPropertyEditable(property: AccountSidebarProperty): boolean {
    return (
        property.editable !== false &&
        (property.kind === 'relationship' ||
            (property.kind === 'custom' && isCustomPropertyEditable(property.provenance)))
    )
}
