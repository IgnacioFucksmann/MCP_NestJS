import { ApiProperty } from '@nestjs/swagger';
import { IsString, IsEmail, Length } from 'class-validator';

export class CreateUsuarioDto {
  @ApiProperty({ 
    description: 'Nombre del usuario',
    maxLength: 100,
    example: 'Juan Pérez'
  })
  @IsString()
  @Length(1, 100)
  nombre: string;

  @ApiProperty({ 
    description: 'Correo electrónico del usuario',
    maxLength: 100,
    example: 'juan@email.com'
  })
  @IsEmail()
  @Length(1, 100)
  email: string;

  @ApiProperty({ 
    description: 'Contraseña del usuario',
    maxLength: 255,
    example: 'contraseña123'
  })
  @IsString()
  @Length(1, 255)
  password: string;
} 