import clsx from 'clsx'

/**
 * Merge class names conditionally (shadcn cn() equivalent)
 */
export function cn(...inputs) {
    return clsx(inputs)
}
