import { ApiProperty } from '@nestjs/swagger';

export class DeleteUsuarioDto {
  @ApiProperty({
    description: 'Mensaje de confirmación de eliminación',
    example: 'Usuario eliminado correctamente'
  })
  mensaje: string;

  @ApiProperty({
    description: 'ID del usuario eliminado',
    example: 1
  })
  usuarioId: number;
} 