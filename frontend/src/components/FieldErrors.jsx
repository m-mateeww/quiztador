export default function FieldErrors({ errors }) {
  if (!errors?.length) return null
  return (
    <ul className="field-errors" role="alert">
      {errors.map((message) => (
        <li key={message}>{message}</li>
      ))}
    </ul>
  )
}
